"""
数据摄入校验器 - 对应 IMPLEMENTATION_SPEC 1.1
"""
import re
from typing import Optional, Union
from fastapi import UploadFile

try:
    import magic
    _has_magic = True
except ImportError:
    magic = None
    _has_magic = False

MAX_SIZES = {
    "text": 2 * 1024 * 1024,
    "image": 20 * 1024 * 1024,
    "video": 500 * 1024 * 1024,
    "table": 50 * 1024 * 1024,
}
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}


class ValidationError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail


def validate_content(content: Optional[str], doc_type: Optional[str] = None) -> None:
    """校验文本内容的必填字段和编码"""
    if content is None:
        raise ValidationError("MISSING_REQUIRED_FIELD", "content is required")
    try:
        content.encode("utf-8")
    except UnicodeEncodeError:
        raise ValidationError("INVALID_ENCODING", "content must be valid UTF-8")
    if doc_type == "text" and len(content.encode("utf-8")) > MAX_SIZES["text"]:
        raise ValidationError("PAYLOAD_TOO_LARGE", f"text exceeds {MAX_SIZES['text']} bytes")


async def validate_file(
    file: Optional[UploadFile], doc_type: str
) -> bytes:
    """校验上传文件: MIME一致性、大小限制"""
    if file is None:
        raise ValidationError("MISSING_REQUIRED_FIELD", "file is required")
    raw = await file.read()
    if len(raw) > MAX_SIZES.get(doc_type, MAX_SIZES["text"]):
        raise ValidationError("PAYLOAD_TOO_LARGE", f"file exceeds limit for type '{doc_type}'")
    mime = None
    if _has_magic:
        mime = magic.from_buffer(raw[:2048], mime=True)
    else:
        # Fallback: MIME from file extension only (production must have libmagic)
        import mimetypes
        if file.filename:
            mime = mimetypes.guess_type(file.filename)[0]
    if doc_type == "image" and mime and mime not in ALLOWED_IMAGE_TYPES:
        raise ValidationError("TYPE_MISMATCH", f"actual MIME {mime} not in allowed image types")
    return raw
