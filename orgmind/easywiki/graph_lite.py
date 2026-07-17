"""
Graph Lite — simplified entity extraction (Section 5.4 of EXECUTION_SPEC)
Rule-based, pure SQLite, no Kuzu/Redis dependency.
"""
import re
import uuid
from typing import List, Tuple
from orgmind.db import get_db
from orgmind.services.write_queue import execute_write


# Regex patterns for entity extraction
PHONE_PATTERN = re.compile(r"1[3-9]\d{9}")
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
DECISION_PATTERN = re.compile(r"(决定|采用|确认|选择|敲定|方案是|最终用)[：:\s]*([^\s，。,\.]{2,30})")
PROJECT_PATTERN = re.compile(r"([^\s]{2,10})(?:项目|系统|平台|模块|服务)")


def extract_entities(text: str) -> List[Tuple[str, str]]:
    """
    Extract entities from text using regex rules.
    Returns list of (entity_name, entity_type), deduplicated within the text.
    """
    entities = []
    seen = set()

    def _add(name, etype):
        key = (name, etype)
        if key not in seen:
            seen.add(key)
            entities.append(key)

    for m in PHONE_PATTERN.findall(text):
        _add(m[:3] + "****" + m[-4:], "Person")

    for m in EMAIL_PATTERN.findall(text):
        _add(m, "Person")

    for _, decision in DECISION_PATTERN.findall(text):
        _add(decision, "Decision")

    for m in PROJECT_PATTERN.findall(text):
        _add(m, "Project")

    return entities


def build_graph(org_id: str, project_id: str, text: str, source_id: str) -> dict:
    """
    Extract entities from text, upsert into easywiki_graph_entities, and create
    pairwise co-occurrence relations (RELATED_WITH) between every distinct pair
    of entities that appear together in this text — NOT a self-loop.
    `source_id` (e.g. a memory/pending-entry id) is recorded on each relation
    for provenance, not as a graph endpoint.
    Returns summary of entities/relations touched.
    """
    entities = extract_entities(text)
    if not entities:
        return {"entities_found": 0, "relations_created": 0}
    if len(entities) == 1:
        # Still upsert the single entity, but no pairwise relation is possible.
        db = get_db()

        def _write_single(db, org_id, project_id, name, etype):
            db.execute(
                "INSERT OR IGNORE INTO easywiki_graph_entities (id,org_id,project_id,name,entity_type) VALUES (?,?,?,?,?)",
                (str(uuid.uuid4()), org_id, project_id, name, etype)
            )
        name, etype = entities[0]
        execute_write(_write_single, org_id, project_id, name, etype)
        return {"entities_found": 1, "relations_created": 0}

    db = get_db()

    def _write_graph(db, org_id, project_id, entities, source_id):
        entity_ids = []
        for name, etype in entities:
            db.execute(
                "INSERT OR IGNORE INTO easywiki_graph_entities (id,org_id,project_id,name,entity_type) VALUES (?,?,?,?,?)",
                (str(uuid.uuid4()), org_id, project_id, name, etype)
            )
            row = db.execute(
                "SELECT id FROM easywiki_graph_entities WHERE name=? AND org_id=? AND entity_type=?",
                (name, org_id, etype)
            ).fetchone()
            if row:
                entity_ids.append(row["id"])

        relations_created = 0
        # Pairwise co-occurrence relations between DISTINCT entities (no self-loops).
        for i in range(len(entity_ids)):
            for j in range(i + 1, len(entity_ids)):
                a, b = entity_ids[i], entity_ids[j]
                if a == b:
                    continue  # defensive: never link an entity to itself
                rid = str(uuid.uuid4())
                db.execute(
                    "INSERT OR IGNORE INTO easywiki_graph_relations (id,from_entity_id,to_entity_id,relation,source_id) VALUES (?,?,?,?,?)",
                    (rid, a, b, "RELATED_WITH", source_id)
                )
                relations_created += 1
        return len(entity_ids), relations_created

    touched, relations = execute_write(_write_graph, org_id, project_id, entities, source_id)
    return {"entities_found": touched, "relations_created": relations}


def query_graph(org_id: str, entity_name: str = None, max_hops: int = 2) -> dict:
    """
    Query the graph for entities and their relations.
    Supports 1-2 hop queries.
    """
    db = get_db()
    results = {"entities": [], "relations": []}

    if entity_name:
        rows = db.execute(
            "SELECT id, name, entity_type FROM easywiki_graph_entities WHERE org_id=? AND name LIKE ?",
            (org_id, f"%{entity_name}%")
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT id, name, entity_type FROM easywiki_graph_entities WHERE org_id=? ORDER BY name LIMIT 50",
            (org_id,)
        ).fetchall()

    entity_ids = [r["id"] for r in rows]
    results["entities"] = [{"id": r["id"], "name": r["name"], "entity_type": r["entity_type"]} for r in rows]

    if entity_ids:
        placeholders = ",".join("?" * len(entity_ids))
        rels = db.execute(
            f"SELECT id, from_entity_id, to_entity_id, relation FROM easywiki_graph_relations WHERE from_entity_id IN ({placeholders}) OR to_entity_id IN ({placeholders}) LIMIT 100",
            entity_ids + entity_ids
        ).fetchall()
        results["relations"] = [{"id": r["id"], "from": r["from_entity_id"], "to": r["to_entity_id"], "relation": r["relation"]} for r in rels]

    return results
