"""
SQLite 写队列 — 防止并发写锁死
所有写操作通过单线程队列串行执行
"""
import asyncio, threading
from collections import deque
from orgmind.database_sqlite import get_db

_write_queue: deque = deque()
_write_lock = threading.Lock()
_write_event = threading.Event()
_write_event.set()


def execute_write(fn, *args, **kwargs):
    """串行执行写操作, 返回 fn 的返回值"""
    with _write_lock:
        db = get_db()
        result = fn(db, *args, **kwargs)
        db.commit()
        return result


def execute_write_batch(operations):
    """批量执行多个写操作 (一个事务)"""
    with _write_lock:
        db = get_db()
        results = []
        for fn, args, kwargs in operations:
            results.append(fn(db, *args, **kwargs))
        db.commit()
        return results
