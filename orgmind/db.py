"""
Unified database abstraction layer.
========================================================================
Self-hosted: SQLite (zero-dependency, default)
Cloud:        PostgreSQL core + SQLite EasyWiki metadata

Set EASYWIKI_DEPLOYMENT=cloud (or DEPLOYMENT_MODE) for cloud mode.
Set EASYWIKI_DB_URL (or DATABASE_URL) for PostgreSQL connection.
========================================================================
"""
import os

_DEPLOYMENT_MODE = os.getenv("EASYWIKI_DEPLOYMENT", os.getenv("DEPLOYMENT_MODE", "self_hosted")).lower()
_DB_URL = os.getenv("EASYWIKI_DB_URL", os.getenv("DATABASE_URL", ""))

_is_cloud = _DEPLOYMENT_MODE in ("cloud", "production", "saas") or _DB_URL.startswith("postgres")

# -- Always import SQLite for EasyWiki tables (works in both modes) -----
from orgmind.database_sqlite import get_db, OrgMindDB

# -- Optionally expose async PostgreSQL for cloud mode ------------------
if _is_cloud:
    from orgmind.database import get_db as _get_async_db_ctx
    def get_async_db():
        return _get_async_db_ctx()
    _MODE_LABEL = f"cloud (EasyWiki: SQLite + Core: PostgreSQL)"
else:
    def get_async_db():
        raise RuntimeError("Async PostgreSQL not available in self-hosted mode. Set EASYWIKI_DEPLOYMENT=cloud.")
    _MODE_LABEL = "self_hosted (SQLite)"


def is_cloud() -> bool:
    return _is_cloud

def mode_label() -> str:
    return _MODE_LABEL


__all__ = ["get_db", "OrgMindDB", "get_async_db", "is_cloud", "mode_label"]

print(f"[EasyWiki DB] Mode: {_MODE_LABEL}")
