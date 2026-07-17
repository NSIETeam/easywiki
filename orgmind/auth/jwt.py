"""
JWT 认证与权限工具
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import jwt as pyjwt
from orgmind.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES


def create_token(
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    role: str,
    department_id: Optional[uuid.UUID] = None,
    project_ids: Optional[list] = None,
    expire_minutes: int = JWT_EXPIRE_MINUTES,
) -> str:
    payload = {
        "user_id": str(user_id),
        "org_id": str(org_id),
        "role": role,
        "department_id": str(department_id) if department_id else None,
        "project_ids": project_ids or [],
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expire_minutes),
        "iat": datetime.now(timezone.utc),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[Dict]:
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except pyjwt.PyJWTError:
        return None


def jwt_payload_to_context(payload: Dict) -> Dict:
    return {
        "user_id": payload["user_id"],
        "org_id": payload["org_id"],
        "role": payload.get("role", "developer"),
        "department_id": payload.get("department_id"),
        "project_ids": payload.get("project_ids", []),
    }
