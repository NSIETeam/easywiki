"""
图查询检索路 - 对应 IMPLEMENTATION_SPEC 4.2 第5步
通过 KuzuDB/FalkorDB 做 1-2 跳关系查询
"""
import re
from typing import List, Dict, Optional
from orgmind.graph.engine import get_graph_engine

GRAPH_QUERY_TRIGGERS = re.compile(r"(谁|哪个|哪些|负责|取代|依赖|属于|关联)")

STOP_WORDS = {
    "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "什么", "吗", "呢", "吧", "啊",
}


def should_trigger_graph(query: str) -> bool:
    """判断 query 是否触发图查询路"""
    return bool(GRAPH_QUERY_TRIGGERS.search(query))


def extract_candidate_entities(query: str) -> List[str]:
    """
    轻量实体名抽取: 分词后去停用词, 取名词短语。
    不做复杂NER, 够用即可。
    """
    import jieba  # type: ignore
    words = jieba.lcut(query)
    entities = [w for w in words if len(w) >= 2 and w not in STOP_WORDS]
    return entities[:10]


async def graph_search(
    org_id: str, query: str,
) -> List[Dict]:
    """
    图查询: 抽取候选实体 → 1-2跳遍历 → 返回结果。
    graph_score 固定为 0.8。
    """
    engine = get_graph_engine()
    entities = extract_candidate_entities(query)
    results = []
    for entity in entities[:5]:
        cypher = f"""
        MATCH (n)-[r*1..2]-(m)
        WHERE n.name CONTAINS $entity AND n.org_id = $org_id
        RETURN DISTINCT m.name AS related, type(r[0]) AS relation
        LIMIT 20
        """
        try:
            rows = engine.query(cypher, {"entity": entity, "org_id": org_id})
            for row in rows:
                results.append({
                    "id": f"graph:{entity}",
                    "content_snippet": f"{entity} --[{row.get('relation','related')}]--> {row.get('related','')}",
                    "source_type": "graph_entity",
                    "graph_score": 0.8,
                    "created_at": None,
                    "access_count": 0,
                })
        except Exception:
            continue
    return results
