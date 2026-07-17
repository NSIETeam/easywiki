"""Unit tests for graph_lite entity extraction and relation building — uses a temp SQLite DB."""
import sys, os, tempfile, uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Point the DB at a temp file before importing database_sqlite
tmp_db = os.path.join(tempfile.mkdtemp(), "test_graph.db")
os.environ["ORGMIND_DB_PATH"] = tmp_db

from orgmind.db import OrgMindDB
import orgmind.database_sqlite as db_module
db_module.DB_PATH = tmp_db
OrgMindDB._instance = None  # force re-init against the temp path

from orgmind.easywiki.graph_lite import extract_entities, build_graph, query_graph

results = []
def check(name, actual, expected):
    results.append((name, actual == expected, actual, expected))

# Test 1: entity extraction basic
ents = extract_entities("决定采用FastAPI技术栈，用于OrgMind项目和测试系统")
check("extract >=2 entities", len(ents) >= 2, True)

# Test 2: dedup within same text
ents2 = extract_entities("决定采用FastAPI, 决定采用FastAPI")
check("dedup within text: unique entries", len(ents2) == len(set(ents2)), True)

# Test 3: build_graph with 2+ entities -> no self-loop relations
org_id = str(uuid.uuid4())
project_id = str(uuid.uuid4())
text = "决定采用React技术栈，应用于OrgMind项目"
result = build_graph(org_id, project_id, text, "source-1")
check("build_graph creates relations for multi-entity text", result["relations_created"] > 0, True)

# Verify no self-loops in DB
db = OrgMindDB.get()
rels = db.execute("SELECT from_entity_id, to_entity_id FROM easywiki_graph_relations").fetchall()
self_loops = [r for r in rels if r["from_entity_id"] == r["to_entity_id"]]
check("NO self-loop relations exist", len(self_loops), 0)

# Test 4: single entity -> no relations, no crash
result_single = build_graph(org_id, project_id, "决定采用X", "source-2")
check("single entity: no relations created", result_single["relations_created"], 0)
check("single entity: entity still recorded", result_single["entities_found"], 1)

# Test 5: query_graph returns entities and relations
q = query_graph(org_id)
check("query_graph returns entities", len(q["entities"]) > 0, True)

# Test 6: relations reference two DIFFERENT entity ids (not same)
if rels:
    check("relations always link two distinct entities", all(r["from_entity_id"] != r["to_entity_id"] for r in rels), True)

passed = sum(1 for _, ok, _, _ in results if ok)
total = len(results)
print(f"\n=== graph_lite unit tests: {passed}/{total} passed ===\n")
for name, ok, actual, expected in results:
    status = "PASS" if ok else "FAIL"
    line = f"[{status}] {name}"
    if not ok:
        line += f"\n    actual:   {actual!r}\n    expected: {expected!r}"
    print(line)

if passed != total:
    sys.exit(1)
