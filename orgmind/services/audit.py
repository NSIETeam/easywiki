"""
审计日志服务
"""
import uuid, json
from orgmind.database_sqlite import get_db


def log_audit(user_id: str, action: str, resource_type: str = None, resource_id: str = None, details: dict = None):
    """记录审计日志"""
    db = get_db()
    db.execute(
        "INSERT INTO audit_logs (id, user_id, action, resource_type, resource_id, details) VALUES (?,?,?,?,?,?)",
        (str(uuid.uuid4()), user_id, action, resource_type, resource_id, json.dumps(details or {}, ensure_ascii=False))
    )
    db.commit()
