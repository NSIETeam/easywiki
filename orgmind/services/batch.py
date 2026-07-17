"""
批量 Embedding 处理, 降低逐条调用的网络开销
"""
from typing import List
from orgmind.services.embedding import get_embeddings
from orgmind.config_production import BATCH_EMBEDDING_SIZE


async def batch_embed(texts: List[str]) -> List[List[float]]:
    """批量处理embedding, 自动按 BATCH_EMBEDDING_SIZE 分片"""
    results = []
    for i in range(0, len(texts), BATCH_EMBEDDING_SIZE):
        batch = texts[i:i + BATCH_EMBEDDING_SIZE]
        batch_results = await get_embeddings(batch)
        results.extend(batch_results)
    return results
