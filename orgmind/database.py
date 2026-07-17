"""
数据库连接与 RLS 会话变量管理
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
from orgmind.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, pool_size=20, max_overflow=10, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def set_db_session_context(
    conn, jwt_payload: Dict
) -> None:
    """
    SET LOCAL 每事务级别,事务结束自动失效,避免连接池复用越权。
    禁止使用 SET (不带 LOCAL),那会导致 A 用户的请求读到 B 用户的 org_id。
    """
    org_id = jwt_payload["org_id"]
    user_id = jwt_payload["user_id"]
    department_id = jwt_payload.get("department_id", "")
    role = jwt_payload.get("role", "developer")
    project_ids = ",".join(jwt_payload.get("project_ids", []))

    await conn.execute(text("SET LOCAL app.org_id = :org_id"), {"org_id": org_id})
    await conn.execute(text("SET LOCAL app.user_id = :user_id"), {"user_id": user_id})
    if department_id:
        await conn.execute(
            text("SET LOCAL app.department_id = :department_id"),
            {"department_id": department_id},
        )
    await conn.execute(text("SET LOCAL app.role = :role"), {"role": role})
    if project_ids:
        await conn.execute(
            text("SET LOCAL app.project_ids = :project_ids"),
            {"project_ids": project_ids},
        )


@asynccontextmanager
async def rls_session(jwt_payload: Dict):
    """
    返回已设置RLS会话变量的AsyncSession。
    用法: async with rls_session(jwt_payload) as session:
    """
    async with async_session_factory() as session:
        async with session.begin():
            await set_db_session_context(
                await session.connection(), jwt_payload
            )
        yield session
