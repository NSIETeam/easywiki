"""
Unified database abstraction layer.
========================================================================
Cloud (default):   PostgreSQL via orgmind.database (set DATABASE_URL)
Development:       SQLite via orgmind.database_sqlite (zero-dep, for main_sqlite.py)

All EasyWiki routes use get_db() from this module.
========================================================================
"""
import os

_DB_URL = os.getenv("DATABASE_URL", "")

# Default: cloud mode. Falls back to SQLite only if DATABASE_URL is empty.
_is_cloud = bool(_DB_URL and _DB_URL.startswith("postgres"))

# Always import SQLite for EasyWiki tables (works in both modes)
from orgmind.database_sqlite import get_db, OrgMindDB

# PostgreSQL async session (cloud mode only)
if _is_cloud:
    from orgmind.database import get_db as _get_async_db_ctx
    def get_async_db():
        return _get_async_db_ctx()
    _MODE_LABEL = f"cloud (PostgreSQL core + SQLite EasyWiki metadata)"
else:
    def get_async_db():
        raise RuntimeError("Async PostgreSQL not available. Set DATABASE_URL or use main_sqlite.py for dev.")
    _MODE_LABEL = "standalone (SQLite)"


def is_cloud() -> bool:
    return _is_cloud

def mode_label() -> str:
    return _MODE_LABEL


__all__ = ["get_db", "OrgMindDB", "get_async_db", "is_cloud", "mode_label"]

print(f"[EasyWiki DB] Mode: {_MODE_LABEL}")
