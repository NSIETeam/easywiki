"""
生产级配置中心 - 补充性能/稳定性相关配置
"""
import os

# ============ 数据库性能 ============
DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
DB_ECHO: bool = os.getenv("DB_ECHO", "false").lower() == "true"

# 读写分离 (Phase2使用)
DB_READ_URL: str = os.getenv("DB_READ_URL", "")

# ============ Redis 缓存 ============
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
QUERY_CACHE_TTL: int = int(os.getenv("QUERY_CACHE_TTL", "300"))
QUERY_CACHE_ENABLED: bool = os.getenv("QUERY_CACHE_ENABLED", "true").lower() == "true"

# ============ 批量处理 ============
BATCH_EMBEDDING_SIZE: int = int(os.getenv("BATCH_EMBEDDING_SIZE", "20"))
ASYNC_WORKERS: int = int(os.getenv("ASYNC_WORKERS", "4"))

# ============ 限流 ============
RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "300"))
RATE_LIMIT_RETRIEVE_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_RETRIEVE_PER_MINUTE", "60"))

# ============ 熔断 ============
CIRCUIT_BREAKER_ENABLED: bool = os.getenv("CIRCUIT_BREAKER_ENABLED", "true").lower() == "true"
CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "30"))

# ============ 优雅关闭 ============
GRACEFUL_SHUTDOWN_TIMEOUT: int = int(os.getenv("GRACEFUL_SHUTDOWN_TIMEOUT", "30"))

# ============ 监控 ============
METRICS_ENABLED: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
