"""
知识图谱引擎 - 统一图接口 (KuzuDB/FalkorDB)
对应 DESIGN.md 4.6, IMPLEMENTATION_SPEC T14
"""
import os
from typing import Dict, List, Optional
from orgmind.config import GRAPH_BACKEND, GRAPH_DB_PATH

_graph_engine = None


class KuzuGraphEngine:
    """KuzuDB 嵌入式图引擎 (Tier0/1)"""

    def __init__(self, db_path: str):
        self._conn = None

    def _ensure_conn(self):
        if self._conn is None:
            try:
                import kuzu  # type: ignore
                self._conn = kuzu.Connection(kuzu.Database(GRAPH_DB_PATH))
                self._init_schema()
            except ImportError:
                raise RuntimeError("kuzu not installed. pip install kuzu")

    def _init_schema(self):
        """初始化图节点/边类型"""
        try:
            self._conn.execute("CREATE NODE TABLE IF NOT EXISTS Entity(name STRING, entity_type STRING, org_id STRING, PRIMARY KEY(name, org_id))")
            self._conn.execute("CREATE REL TABLE IF NOT EXISTS RELATED(FROM Entity TO Entity, relation STRING)")
        except Exception:
            pass

    def query(self, cypher: str, params: Optional[Dict] = None) -> List[Dict]:
        self._ensure_conn()
        try:
            result = self._conn.execute(cypher)
            columns = result.get_column_names()
            rows = []
            while result.has_next():
                row = result.get_next()
                rows.append({columns[i]: row[i] for i in range(len(columns))})
            return rows
        except Exception:
            return []

    def add_node(self, name: str, entity_type: str, org_id: str) -> None:
        self._ensure_conn()
        try:
            self._conn.execute(
                f"MERGE (n:Entity {{name: $name, org_id: $org_id}}) SET n.entity_type = $entity_type",
                {"name": name, "entity_type": entity_type, "org_id": org_id},
            )
        except Exception:
            pass

    def add_edge(self, from_name: str, to_name: str, org_id: str, relation: str) -> None:
        self._ensure_conn()
        try:
            self._conn.execute(
                "MATCH (a:Entity {name: $from, org_id: $org_id}) "
                "MATCH (b:Entity {name: $to, org_id: $org_id}) "
                "MERGE (a)-[:RELATED {relation: $rel}]->(b)",
                {"from": from_name, "to": to_name, "org_id": org_id, "rel": relation},
            )
        except Exception:
            pass


class FalkorGraphEngine:
    """FalkorDB 图引擎 (Tier2+) - 占位实现"""

    def __init__(self):
        pass

    def query(self, cypher: str, params: Dict) -> List[Dict]:
        return []

    def add_node(self, name: str, entity_type: str, org_id: str) -> None:
        pass

    def add_edge(self, from_name: str, to_name: str, org_id: str, relation: str) -> None:
        pass


def get_graph_engine():
    global _graph_engine
    if _graph_engine is None:
        if GRAPH_BACKEND == "kuzu":
            _graph_engine = KuzuGraphEngine(GRAPH_DB_PATH)
        else:
            _graph_engine = FalkorGraphEngine()
    return _graph_engine
