"""
Write queue — serializes writes to prevent SQLite lock contention.
Works in both self-hosted (SQLite) and cloud (PostgreSQL) modes.
"""
import threading
from collections import deque
from orgmind.db import get_db

_write_queue: deque = deque()
_write_lock = threading.Lock()
_write_event = threading.Event()
_write_event.set()


def execute_write(fn, *args, **kwargs):
    """Serialize write operations, return fn's result (one transaction)."""
    with _write_lock:
        db = get_db()
        result = fn(db, *args, **kwargs)
        db.commit()
        return result


def execute_write_batch(operations):
    """Execute multiple writes in one transaction."""
    with _write_lock:
        db = get_db()
        results = []
        for fn, args, kwargs in operations:
            results.append(fn(db, *args, **kwargs))
        db.commit()
        return results
