"""
检索路由 - 对应 IMPLEMENTATION_SPEC 4.2 全部8步
三路混合检索: vector + keyword + (可选) graph
"""
import time
import asyncio
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from orgmind.retrieval.vector import vector_search_memories, vector_search_documents
from orgmind.retrieval.keyword import keyword_search_memories
from orgmind.retrieval.graph import should_trigger_graph, graph_search
from orgmind.retrieval.fusion import compute_final_scores, apply_token_budget
from orgmind.config import MAX_CONTEXT_CHARS


async def retrieve(
    session: AsyncSession,
    jwt_payload: Dict,
    query: str,
    top_k: int = 5,
    filters: Optional[Dict] = None,
    mode: str = "auto",
) -> Dict:
    """
    统一检索入口, 完整8步流程。
    返回: { results, total_candidates, retrieval_time_ms, degraded }
    """
    start_time = time.monotonic()
    degraded = False
    total_candidates = 0
    final_results: List[Dict] = []

    top_k = min(top_k, 20)
    top_k_fetch = top_k * 4
    org_id = jwt_payload["org_id"]

    trigger_graph = (mode == "graph_only") or (
        mode == "auto" and should_trigger_graph(query)
    )
    do_vector = mode in ("auto", "vector_only")
    do_keyword = mode in ("auto", "keyword_only")

    vector_results = []
    keyword_results = []
    graph_results = []

    tasks = []

    async def _vector():
        nonlocal degraded
        try:
            mem_results = await vector_search_memories(session, query, top_k_fetch)
            doc_results = await vector_search_documents(session, query, top_k_fetch)
            return mem_results + doc_results
        except Exception:
            degraded = True
            return []

    async def _keyword():
        try:
            return await keyword_search_memories(session, query, top_k_fetch)
        except Exception:
            return []

    async def _graph():
        nonlocal degraded
        try:
            return await graph_search(org_id, query)
        except Exception:
            degraded = True
            return []

    if do_vector:
        tasks.append(_vector())
    if do_keyword:
        tasks.append(_keyword())
    if trigger_graph:
        tasks.append(_graph())

    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    idx = 0
    if do_vector:
        vector_results = results_list[idx] if not isinstance(results_list[idx], Exception) else []
        idx += 1
        if isinstance(results_list[idx - 1], Exception):
            degraded = True
            # 嵌入服务故障降级: 只跑关键词
            if do_keyword:
                keyword_results = results_list[idx] if not isinstance(results_list[idx], Exception) else []
                final_results = keyword_results
                total_candidates = len(final_results)
                if not keyword_results:
                    from fastapi import HTTPException
                    raise HTTPException(status_code=503, detail="SERVICE_UNAVAILABLE: all retrieval paths failed")
                elapsed = (time.monotonic() - start_time) * 1000
                return {
                    "results": sorted(
                        [{"id": r["id"], "content_snippet": r.get("content_snippet", ""),
                          "source_type": r.get("source_type", "memory"),
                          "score": r.get("keyword_score", 0),
                          "score_breakdown": {"vector": 0, "keyword": r.get("keyword_score", 0), "graph": 0, "recency": 0},
                          "citation": {"source_id": r["id"], "location": ""}}
                         for r in final_results[:top_k]],
                        key=lambda x: x["score"], reverse=True,
                    ),
                    "total_candidates": total_candidates,
                    "retrieval_time_ms": round(elapsed),
                    "degraded": True,
                }
    if do_keyword:
        keyword_results = results_list[idx] if not isinstance(results_list[idx], Exception) else []
        idx += 1
    if trigger_graph:
        graph_results = results_list[idx] if not isinstance(results_list[idx], Exception) else []
        idx += 1

    # 第6步: 融合排序
    final_results = compute_final_scores(vector_results, keyword_results, graph_results)
    total_candidates = len(final_results)

    # 第7步: Token预算
    final_results = apply_token_budget(final_results, top_k, MAX_CONTEXT_CHARS)

    # 第8步: 组装响应
    elapsed = (time.monotonic() - start_time) * 1000
    formatted = []
    for r in final_results:
        formatted.append({
            "id": r["id"],
            "content_snippet": r.get("content_snippet", ""),
            "source_type": r.get("source_type", "memory"),
            "score": r["score"],
            "score_breakdown": r.get("score_breakdown", {}),
            "citation": {"source_id": r["id"], "location": ""},
        })

    return {
        "results": formatted,
        "total_candidates": total_candidates,
        "retrieval_time_ms": round(elapsed),
        "degraded": degraded,
    }
