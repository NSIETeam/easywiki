"""
去重算法 - 对应 IMPLEMENTATION_SPEC 1.3
精确步骤: SHA256哈希匹配 → 向量近似重复检测
"""
import hashlib
import unicodedata
from enum import Enum
from typing import Optional, Tuple, List
from orgmind.config import DUPLICATE_THRESHOLD_NEAR, DUPLICATE_THRESHOLD_RELATED, DEDUP_TOPK


class DupResult(Enum):
    EXACT = "exact"
    NEAR_DUPLICATE = "near_duplicate"
    RELATED = "related"
    NEW = "new"


def compute_content_hash(content: str) -> str:
    """SHA256(NFKC规范化后的正文)"""
    normalized = unicodedata.normalize("NFKC", content)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


async def check_memory_duplicate(
    session,
    org_id: str,
    content_hash: str,
    embedding: Optional[list] = None,
) -> Tuple[DupResult, Optional[str], Optional[list]]:
    """
    检查记忆去重。返回 (去重结果, 重复记录id, 关联记录id列表)。
    步骤: 1) 哈希精确匹配 2) 向量近似匹配
    """
    from sqlalchemy import select, func
    from orgmind.models.memory import Memory
    if existing:
        return DupResult.EXACT, str(existing), None

    # 第2步: 无embedding则跳过近似检测
    if embedding is None:
        return DupResult.NEW, None, None

    # 第3步: 向量近似匹配
    stmt = select(
        Memory.id,
        1 - func.cosine_distance(Memory.embedding, embedding),
    ).where(
        Memory.org_id == org_id,
        Memory.embedding.isnot(None),
    ).order_by(
        func.cosine_distance(Memory.embedding, embedding),
    ).limit(DEDUP_TOPK)
    result = await session.execute(stmt)
    rows = result.all()

    if not rows:
        return DupResult.NEW, None, None

    top_id, top_sim = rows[0]
    related_ids = [str(r[0]) for r in rows[1:]]

    if top_sim and top_sim >= DUPLICATE_THRESHOLD_NEAR:
        return DupResult.NEAR_DUPLICATE, str(top_id), related_ids
    elif top_sim and top_sim >= DUPLICATE_THRESHOLD_RELATED:
        return DupResult.RELATED, None, related_ids

    return DupResult.NEW, None, None
