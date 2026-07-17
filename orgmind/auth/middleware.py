"""
RLS 权限中间件 - 每个请求注入 SET LOCAL app.*
"""
from typing import Dict
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from orgmind.auth.jwt import verify_token, jwt_payload_to_context
from orgmind.database import set_db_session_context
from sqlalchemy.ext.asyncio import AsyncSession
from orgmind.database import async_session_factory

security = HTTPBearer(auto_error=False)


async def get_jwt_payload(request: Request) -> Dict:
    """
    从请求头提取JWT并验证, 返回payload。
    注意: org_id 只能从 JWT 中解析, 绝不接受请求体/URL参数中的 org_id。
    """
    credentials: HTTPAuthorizationCredentials = await security(request)
    if not credentials:
        raise HTTPException(status_code=401, detail="MISSING_AUTH_HEADER")
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="INVALID_TOKEN")
    return payload


async def rls_middleware(request: Request, call_next):
    """
    FastAPI 中间件: 每个请求开始时设置 RLS 会话变量。
    在连接池场景下必须用 SET LOCAL (事务级别),
    不能用 SET (会话级别会导致跨请求越权)。
    """
    # 跳过不需要认证的路径
    if request.url.path in ("/health", "/api/v1/auth/login", "/api/v1/auth/register"):
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header or not auth_header.startswith("Bearer "):
        return await call_next(request)

    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token)
    if payload is None:
        return await call_next(request)

    context = jwt_payload_to_context(payload)
    request.state.jwt_payload = context

    # 在下一个数据库查询时自动设置 RLS 变量
    request.state._rls_context = context

    response = await call_next(request)
    return response
