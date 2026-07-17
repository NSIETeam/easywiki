"""
向量检索路 - 对应 IMPLEMENTATION_SPEC 4.2 第3步
"""
from typing import List, Optional, Dict
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from orgmind.models.memory import Memory
from orgmind.models.document import DocumentChunk
from orgmind.services.embedding import get_embedding


async def vector_search_memories(
    session: AsyncSession, query: str, top_k: int = 20,
) -> List[Dict]:
    """pgvector HNSW 语义检索记忆"""
    query_emb = await get_embedding(query)
    stmt = (
        select(
            Memory.id,
            Memory.content,
            Memory.type,
            Memory.created_at,
            Memory.access_count,
            (1 - func.cosine_distance(Memory.embedding, query_emb)).label("vector_score"),
        )
        .where(Memory.status == "active", Memory.embedding.isnot(None))
        .order_by(func.cosine_distance(Memory.embedding, query_emb))
        .limit(top_k)
    )
    result = await session.execute(stmt)
    rows = result.all()
    return [
        {
            "id": str(r[0]),
            "content_snippet": r[1][:300] if r[1] else "",
            "source_type": "memory",
            "vector_score": float(r[4]) if r[4] else 0.0,
            "type": r[2],
            "created_at": r[3],
            "access_count": r[3] if r[3] else 0,
        }
        for r in rows
    ]


async def vector_search_documents(
    session: AsyncSession, query: str, top_k: int = 20,
) -> List[Dict]:
    """pgvector HNSW 检索文档切片"""
    query_emb = await get_embedding(query)
    stmt = (
        select(
            DocumentChunk.id,
            DocumentChunk.content,
            DocumentChunk.document_id,
            DocumentChunk.chunk_index,
            (1 - func.cosine_distance(DocumentChunk.embedding, query_emb)).label("vector_score"),
        )
        .where(DocumentChunk.embedding.isnot(None))
        .order_by(func.cosine_distance(DocumentChunk.embedding, query_emb))
        .limit(top_k)
    )
    result = await session.execute(stmt)
    rows = result.all()
    return [
        {
            "id": str(r[0]),
            "content_snippet": r[1][:300] if r[1] else "",
            "source_type": "document_chunk",
            "vector_score": float(r[4]) if r[4] else 0.0,
            "document_id": str(r[2]),
            "chunk_index": r[3],
        }
        for r in rows
    ]
