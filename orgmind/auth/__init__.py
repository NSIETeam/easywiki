"""Auth utilities — sync (works without PostgreSQL)."""

import jwt as pyjwt
from typing import Dict
from fastapi import HTTPException
from orgmind.config import JWT_SECRET, JWT_ALGORITHM

# Re-export from jwt module (sync, no PG needed)
from orgmind.auth.jwt import create_token, verify_token, jwt_payload_to_context

# Conditional PostgreSQL-dependent imports
try:
    from orgmind.auth.middleware import get_jwt_payload, rls_middleware
except Exception:
    get_jwt_payload = None  # type: ignore
    rls_middleware = None  # type: ignore


def decode_auth_header(authorization: str | None) -> Dict:
    """
    Extract and verify JWT from Authorization header.
    Used by easywiki routes and main_sqlite.
    Raises HTTPException(401) on invalid/missing token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "MISSING_AUTH")
    try:
        return pyjwt.decode(authorization[7:], JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except pyjwt.PyJWTError:
        raise HTTPException(401, "INVALID_TOKEN")


__all__ = [
    "create_token", "verify_token", "jwt_payload_to_context",
    "decode_auth_header",
    "get_jwt_payload", "rls_middleware",
]
