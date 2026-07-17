"""
Demo 模式配置 - 覆盖生产配置
- 零外部依赖: SHA256伪向量替代sentence-transformers
- 演示场景: 功能完整但向量精度低
- 生产切换: 设置 ORGMIND_DEMO_MODE=false + pip install sentence-transformers
"""
import os

# Force pseudo embedding mode
os.environ["ORGMIND_EMBEDDING_MODEL"] = "pseudo"

# Demo branding
DEMO_MODE = True
DEMO_COMPANY_NAME = os.getenv("ORGMIND_DEMO_COMPANY", "示例企业")
DEMO_ADMIN_EMAIL = os.getenv("ORGMIND_DEMO_ADMIN", "admin@demo.com")

# Skip heavy imports in demo
SKIP_SENTENCE_TRANSFORMERS = True
SKIP_TORCH = True
