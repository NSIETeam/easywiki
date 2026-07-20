"""
Skill 三层渐进加载引擎 - 对应 IMPLEMENTATION_SPEC 第五节 + DESIGN.md 4.2
Level1(目录常驻Redis) → Level2(正文按需) → Level3(附属资源延迟)
"""
import json
import math
from datetime import datetime, timezone
from typing import List, Dict, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from orgmind.models.artifact import Artifact, ArtifactPermission
from orgmind.config import SKILL_CATALOG_REDIS_KEY, SKILL_CATALOG_TTL
import redis.asyncio as aioredis  # type: ignore
from orgmind.config import REDIS_URL

redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)


async def get_skill_catalog(
    session: AsyncSession, org_id: str,
) -> List[Dict]:
    """第1步: 从Redis获取Level1目录, 缓存不存在则从Postgres加载"""
    cache_key = SKILL_CATALOG_REDIS_KEY.format(org_id=org_id)
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    stmt = select(
        Artifact.id, Artifact.name, Artifact.description,
        Artifact.tags, Artifact.usage_count, Artifact.updated_at,
        Artifact.status, Artifact.scope, Artifact.object_type,
    ).where(
        Artifact.org_id == org_id,
        Artifact.status == "published",
    )
    result = await session.execute(stmt)
    rows = result.all()
    catalog = [
        {
            "id": str(r[0]),
            "name": r[1],
            "description": r[2],
            "tags": r[3] or [],
            "usage_count": r[4] or 0,
            "updated_at": r[5].isoformat() if r[5] else None,
            "status": r[6],
            "scope": r[7],
            "object_type": r[8],
        }
        for r in rows
    ]
    await redis_client.setex(cache_key, SKILL_CATALOG_TTL, json.dumps(catalog, default=str))
    return catalog


async def match_skills(
    session: AsyncSession,
    org_id: str,
    query: str,
    user_role: str,
    top_k: int = 5,
) -> List[Dict]:
    """
    第2步: tags精确匹配优先 → 没命中就向量检索 description_embedding
    第3步: 权限过滤 + 重排序
    """
    catalog = await get_skill_catalog(session, org_id)
    query_lower = query.lower()

    # tags 精确匹配优先
    tag_matches = []
    for item in catalog:
        item_tags = [t.lower() for t in (item.get("tags") or [])]
        if any(t in query_lower for t in item_tags):
            tag_matches.append(item)

    if tag_matches:
        candidates = tag_matches
    else:
        # 向量检索 (简单版: 对 description 做退化的关键词降级, 正式版用embedding)
        candidates = [
            c for c in catalog
            if any(w in c.get("description", "").lower() for w in query_lower.split())
        ] or catalog[:20]

    # 第3步: 权限过滤 (对照 artifact_permissions 表)
    stmt = select(ArtifactPermission).where(
        ArtifactPermission.artifact_id.in_([c["id"] for c in candidates]),
        ArtifactPermission.role == user_role,
        ArtifactPermission.access == "read",
    )
    result = await session.execute(stmt)
    allowed_ids = {str(p.artifact_id) for p in result.scalars().all()}
    allowed_ids |= {c["id"] for c in candidates if c.get("scope") == "org"}

    candidates = [c for c in candidates if c["id"] in allowed_ids]

    # 重排序: usage_count * exp(-days_since_last_used/30)
    now = datetime.now(timezone.utc)
    for c in candidates:
        updated = c.get("updated_at")
        days = 0
        if updated:
            days = (now - datetime.fromisoformat(updated).replace(tzinfo=timezone.utc)).days
        c["_score"] = (c.get("usage_count", 0) + 1) * math.exp(-days / 30)

    candidates.sort(key=lambda x: x.get("_score", 0), reverse=True)
    return candidates[:top_k]


async def load_skill_level2(
    session: AsyncSession, skill_ids: List[str],
) -> List[Dict]:
    """第4步: 按需加载 Level2 正文 content 字段"""
    if not skill_ids:
        return []
    stmt = select(Artifact).where(Artifact.id.in_(skill_ids))
    result = await session.execute(stmt)
    artifacts = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "name": a.name,
            "description": a.description,
            "content": a.content,
            "resources": a.resources,
            "object_type": a.object_type,
            "bound_skill_ids": a.bound_skill_ids,
            "tools": a.tools,
        }
        for a in artifacts
    ]
