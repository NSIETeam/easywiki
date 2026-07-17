"""
PII 敏感信息检测 - 对应 IMPLEMENTATION_SPEC 1.4
正则表按规范精确匹配, 命中后提升 sensitivity 级别
"""
import re
from typing import Optional

PII_PATTERNS = {
    "phone_cn": re.compile(r"1[3-9]\d{9}"),
    "id_card_cn": re.compile(
        r"[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[012])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]"
    ),
    "email": re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
    "bank_card": re.compile(r"\b\d{16,19}\b"),
    "api_key": re.compile(
        r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[\w\-]{16,}"
    ),
}


def detect_pii(text: str) -> list[str]:
    """检测文本中的PII类型, 返回命中的类型列表"""
    hits = []
    for ptype, pattern in PII_PATTERNS.items():
        if pattern.search(text):
            hits.append(ptype)
    return hits


def censor_pii(text: str) -> str:
    """生成脱敏预览文本, 仅用于展示, 不替代RLS安全边界"""
    text = PII_PATTERNS["phone_cn"].sub(lambda m: m.group()[:3] + "****" + m.group()[-4:], text)
    text = PII_PATTERNS["id_card_cn"].sub(lambda m: m.group()[:6] + "********" + m.group()[-4:], text)
    text = PII_PATTERNS["email"].sub(lambda m: m.group()[0] + "***@" + m.group().split("@")[-1], text)
    text = PII_PATTERNS["bank_card"].sub(lambda m: m.group()[:4] + "****" + m.group()[-4:], text)
    text = PII_PATTERNS["api_key"].sub(lambda m: m.group().split(":")[0] + ":****", text)
    return text


def upgrade_sensitivity(
    current_sensitivity: str, pii_hits: list[str]
) -> str:
    """
    PII命中 → sensitivity提升。
    normal→sensitive, 已经是sensitive/confidential的不降级。
    """
    if not pii_hits:
        return current_sensitivity
    if current_sensitivity == "normal":
        return "sensitive"
    return current_sensitivity
