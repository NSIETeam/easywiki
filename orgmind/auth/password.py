"""
密码安全 — bcrypt 哈希 + 验证
"""
import bcrypt
import hmac
import hashlib


def hash_password(password: str) -> str:
    """bcrypt 哈希密码, 返回 str (兼容 SQLite TEXT 列)"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """验证密码, 兼容旧的 SHA256 哈希 (自动迁移)"""
    # New format: bcrypt ($2b$...)
    if hashed.startswith("$2"):
        return bcrypt.checkpw(password.encode(), hashed.encode())

    # Legacy: SHA256 (auto-migrate on next login)
    legacy_hash = hashlib.sha256(password.encode()).hexdigest()
    if hmac.compare_digest(legacy_hash, hashed):
        return True

    return False
