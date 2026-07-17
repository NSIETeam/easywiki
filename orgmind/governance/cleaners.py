"""
文本清洗器 - 对应 IMPLEMENTATION_SPEC 1.2
"""
import re
import unicodedata
from typing import Optional, Tuple
from orgmind.config import MAX_TEXT_LENGTH


def clean_text(text: str) -> Tuple[str, dict]:
    """
    清洗文本内容，返回 (cleaned_text, metadata)
    规则: 去除控制字符(保留 \n \t), 折叠连续空行, trim, Unicode NFKC
    """
    meta: dict = {}
    if not text:
        return text, meta

    # 长度截断
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]
        meta["truncated"] = True

    # Unicode NFKC 规范化
    text = unicodedata.normalize("NFKC", text)

    # 去除除 \n \t 外的控制字符
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

    # 折叠连续空行: ≥3行 → 2行
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 首尾 trim
    text = text.strip()

    return text, meta
