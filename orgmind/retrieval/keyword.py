"""
关键词检索路 - 对应 IMPLEMENTATION_SPEC 4.2 第4步
Postgres tsvector BM25 检索, 用于专有名词/代码符号等向量检索弱的场景
"""
from typing import List, Dict
from sqlalchemy import select, func, text, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from orgmind.models.memory import Memory


async def keyword_search_memories(
    session: AsyncSession, query: str, top_k: int = 20,
) -> List[Dict]:
    """
    Postgres全文检索记忆。
    用 plainto_tsquery 处理自然语言查询, 再用 ts_rank 排序。
    """
    stmt = (
        select(
            Memory.id,
            Memory.content,
            Memory.created_at,
            Memory.access_count,
            func.ts_rank(
                func.to_tsvector("simple", func.coalesce(Memory.content, "")),
                func.plainto_tsquery("simple", query),
            ).label("keyword_score"),
        )
        .where(
            func.to_tsvector("simple", func.coalesce(Memory.content, "")).op("@@")(
                func.plainto_tsquery("simple", query)
            ),
            Memory.status == "active",
        )
        .order_by(text("keyword_score DESC"))
        .limit(top_k)
    )
    result = await session.execute(stmt)
    rows = result.all()
    return [
        {
            "id": str(r[0]),
            "content_snippet": r[1][:300] if r[1] else "",
            "source_type": "memory",
            "keyword_score": float(r[4]) if r[4] else 0.0,
            "created_at": r[2],
            "access_count": r[3] if r[3] else 0,
        }
        for r in rows
    ]
