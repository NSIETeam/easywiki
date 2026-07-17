"""
融合排序 - 对应 IMPLEMENTATION_SPEC 4.2 第6步 + 第7步
final_score = 0.5*v + 0.2*k + 0.2*g + 0.1*recency
"""
import math
from datetime import datetime, timezone
from typing import List, Dict, Optional


def compute_final_scores(
    vector_results: List[Dict],
    keyword_results: List[Dict],
    graph_results: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    三路结果融合排序。
    按 id 去重合并, 每路分数取该结果在各路中的最高分。
    """
    merged: Dict[str, Dict] = {}
    graph_results = graph_results or []

    def _add(source: str, items: List[Dict]):
        score_key = f"{source}_score"
        for item in items:
            rid = item["id"]
            if rid not in merged:
                merged[rid] = {
                    "id": rid,
                    "content_snippet": item.get("content_snippet", ""),
                    "source_type": item.get("source_type", "memory"),
                    "vector_score": 0.0,
                    "keyword_score": 0.0,
                    "graph_score": 0.0,
                    "created_at": item.get("created_at"),
                    "access_count": item.get("access_count", 0),
                }
            merged[rid][score_key] = max(
                merged[rid].get(score_key, 0.0),
                item.get(score_key, 0.0),
            )

    _add("vector", vector_results)
    _add("keyword", keyword_results)
    _add("graph", graph_results)

    now = datetime.now(timezone.utc)
    results = []
    for item in merged.values():
        created_at = item.get("created_at")
        days_since = 0
        if created_at:
            days_since = (now - created_at).total_seconds() / 86400
        recency_score = math.exp(-days_since / 90)

        final_score = (
            0.5 * item["vector_score"]
            + 0.2 * item["keyword_score"]
            + 0.2 * item["graph_score"]
            + 0.1 * recency_score
        )
        item["score"] = round(final_score, 4)
        item["score_breakdown"] = {
            "vector": round(item["vector_score"], 4),
            "keyword": round(item["keyword_score"], 4),
            "graph": round(item["graph_score"], 4),
            "recency": round(recency_score, 4),
        }
        results.append(item)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def apply_token_budget(
    results: List[Dict], top_k: int = 5, max_chars: int = 8000,
) -> List[Dict]:
    """
    Top-K截断 + Token预算控制。
    先取 top_k, 再按分数从低到高剔除直到总字符数不超预算。
    不平均裁剪, 整条剔除。
    """
    results = results[:top_k]
    total_chars = sum(len(r.get("content_snippet", "")) for r in results)
    while total_chars > max_chars and len(results) > 1:
        removed = results.pop()
        total_chars -= len(removed.get("content_snippet", ""))
    return results
