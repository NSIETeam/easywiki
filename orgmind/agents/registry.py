"""
Agent 注册中心 - 对应 DESIGN.md 4.3
支持定义/衍生(fork)/调用可复用 Agent
"""
import uuid
from typing import List, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from orgmind.models.artifact import Artifact
from orgmind.skills.engine import match_skills, load_skill_level2


async def register_agent(
    session: AsyncSession,
    org_id: str,
    name: str,
    description: str,
    content: str,
    tools: List[str],
    bound_skill_ids: List[str],
    author_id: str,
    parent_id: Optional[str] = None,
    scope: str = "department",
) -> Dict:
    """注册新 Agent (创建 artifacts 记录)"""
    artifact = Artifact(
        id=uuid.uuid4(),
        org_id=uuid.UUID(org_id),
        object_type="agent",
        name=name,
        description=description,
        content=content,
        version="1.0.0",
        status="draft",
        scope=scope,
        author_id=uuid.UUID(author_id),
        tools=tools,
        bound_skill_ids=[uuid.UUID(sid) for sid in bound_skill_ids],
        parent_id=uuid.UUID(parent_id) if parent_id else None,
    )
    session.add(artifact)
    await session.commit()
    return {"id": str(artifact.id), "name": name, "status": "draft"}


async def invoke_agent(
    session: AsyncSession,
    org_id: str,
    agent_name: str,
    user_role: str,
) -> Dict:
    """
    调用 Agent: 按 name 解析 → 拉取 Level2 system_prompt + 绑定 Skill 列表
    → 组装会话上下文
    """
    stmt = select(Artifact).where(
        Artifact.org_id == uuid.UUID(org_id),
        Artifact.name == agent_name,
        Artifact.object_type == "agent",
        Artifact.status == "published",
    )
    result = await session.execute(stmt)
    agent = result.scalars().first()
    if not agent:
        raise ValueError(f"Agent '{agent_name}' not found")

    # 加载绑定的 Skill (Level2)
    bound_skills = []
    if agent.bound_skill_ids:
        bound_skills = await load_skill_level2(
            session, [str(sid) for sid in agent.bound_skill_ids]
        )

    return {
        "agent_id": str(agent.id),
        "name": agent.name,
        "system_prompt": agent.content,
        "tools": agent.tools or [],
        "bound_skills": bound_skills,
    }
