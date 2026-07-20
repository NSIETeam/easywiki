"""
Embedding 服务 — v2.1
优先: sentence-transformers 本地模型 (离线, 免费, 中文效果好)
降级: OpenAI text-embedding-3-small
再降级: SHA256 伪向量 (仅用于测试)
"""
import os, hashlib, random, logging, threading
from typing import List
from orgmind.config import EMBEDDING_MODEL, EMBEDDING_DIM

logger = logging.getLogger(__name__)

_model = None
_model_loaded = False
_use_openai = False
_openai_client = None
_model_lock = threading.Lock()


def _load_model():
    global _model, _model_loaded, _use_openai, _openai_client
    if _model_loaded:
        return

    with _model_lock:
        if _model_loaded:  # Double-check after acquiring lock
            return

    # Demo mode: skip heavy models, use pseudo vectors
    if os.getenv("ORGMIND_DEMO_MODE", "").lower() == "true" or EMBEDDING_MODEL == "pseudo":
        _model_loaded = True
        logger.info("Embedding: demo mode - using SHA256 pseudo vectors")
        return

    # Try sentence-transformers first
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
        _model_loaded = True
        logger.info(f"Embedding: loaded local model {EMBEDDING_MODEL}")
        return
    except Exception as e:
        logger.warning(f"Embedding: sentence-transformers failed: {e}")

    # Try OpenAI
    if os.getenv("OPENAI_API_KEY"):
        try:
            import openai
            _openai_client = openai.OpenAI()
            _use_openai = True
            _model_loaded = True
            logger.info("Embedding: using OpenAI text-embedding-3-small")
            return
        except Exception as e:
            logger.warning(f"Embedding: OpenAI failed: {e}")

    # Fallback: pseudo vectors
    _model_loaded = True
    logger.warning("Embedding: using SHA256 pseudo vectors (NOT for production)")


def get_embedding_sync(text: str) -> List[float]:
    """同步获取 embedding"""
    _load_model()

    if _model is not None:
        vec = _model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    if _use_openai and _openai_client:
        try:
            resp = _openai_client.embeddings.create(model="text-embedding-3-small", input=[text])
            return resp.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")

    # Pseudo fallback
    h = hashlib.sha256(text.encode()).digest()
    seed = int.from_bytes(h[:8], 'big')
    rng = random.Random(seed)
    return [rng.uniform(-1, 1) for _ in range(EMBEDDING_DIM)]


async def get_embedding(text: str) -> List[float]:
    """异步版 (兼容旧接口)"""
    return get_embedding_sync(text)


async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """批量获取 embedding"""
    _load_model()
    if _model is not None:
        vecs = _model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vecs]

    return [get_embedding_sync(t) for t in texts]
