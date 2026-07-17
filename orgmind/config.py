"""
OrgMind 配置 — v2.1 企业级
JWT密钥自动生成, bcrypt密码, 安全配置
"""
import os, secrets, json
from pathlib import Path

CONFIG_DIR = Path(os.getenv("ORGMIND_CONFIG_DIR", os.path.expanduser("~/.orgmind")))
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
SECRET_FILE = CONFIG_DIR / "secret.key"
CONFIG_FILE = CONFIG_DIR / "config.json"

def _load_or_create_secret() -> str:
    if SECRET_FILE.exists():
        return SECRET_FILE.read_text().strip()
    s = secrets.token_hex(32)
    SECRET_FILE.write_text(s)
    SECRET_FILE.chmod(0o600)
    return s

def _load_or_create_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    cfg = {"version": "2.1.0", "created_at": str(os.path.getmtime(__file__))}
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    return cfg

JWT_SECRET = _load_or_create_secret()
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("ORGMIND_JWT_EXPIRE", "1440"))  # 24h default

EMBEDDING_MODEL = os.getenv("ORGMIND_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
EMBEDDING_DIM = 384  # MiniLM-L12-v2 output dim

DEPLOY_TIER = os.getenv("ORGMIND_DEPLOY_TIER", "solo")

# LLM config for auto-memory extraction
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("ORGMIND_LLM_MODEL", "gpt-4o-mini")

# SSO/OAuth
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
DINGTALK_APP_ID = os.getenv("DINGTALK_APP_ID", "")
DINGTALK_APP_SECRET = os.getenv("DINGTALK_APP_SECRET", "")

_config = _load_or_create_config()

# Misc limits
MAX_TEXT_LENGTH = int(os.getenv("ORGMIND_MAX_TEXT_LENGTH", "10000"))

# Dedup thresholds
DUPLICATE_THRESHOLD_NEAR = 0.95
DUPLICATE_THRESHOLD_RELATED = 0.80
DEDUP_TOPK = 20

# Database URLs (for SQLAlchemy/PostgreSQL modules compatibility)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{CONFIG_DIR / 'orgmind.db'}")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Graph engine config
GRAPH_BACKEND = os.getenv("ORGMIND_GRAPH_BACKEND", "falkor")
GRAPH_DB_PATH = os.getenv("ORGMIND_GRAPH_DB_PATH", str(CONFIG_DIR / "graph"))

# Retrieval config
MAX_CONTEXT_CHARS = int(os.getenv("ORGMIND_MAX_CONTEXT_CHARS", "8000"))

# Skill catalog cache
SKILL_CATALOG_REDIS_KEY = os.getenv("ORGMIND_SKILL_CATALOG_KEY", "orgmind:skill:catalog:{org_id}")
SKILL_CATALOG_TTL = int(os.getenv("ORGMIND_SKILL_CATALOG_TTL", "300"))
