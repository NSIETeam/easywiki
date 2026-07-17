"""
自动记忆提取 — v2.1
优先: LLM 结构化提取 (OpenAI)
降级: 正则规则提取
"""
import json, re, logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# === LLM 提取 ===
LLM_PROMPT = """You are a memory extraction engine. Extract all decisions, bug fixes, best practices, and architecture choices from the conversation below.

Return a JSON array. Each item must have:
- "type": one of "decision", "bug_fix", "best_practice", "architecture"
- "content": concise statement of the memory (in the original language)
- "confidence": float 0.0-1.0

If nothing extractable, return [].

Conversation:
"""


def extract_memories_from_session(session_text: str) -> List[Dict]:
    """从会话文本中提取记忆, 优先用 LLM"""
    # Try LLM first
    try:
        return _extract_with_llm(session_text)
    except Exception as e:
        logger.warning(f"LLM extraction failed, falling back to rules: {e}")

    # Fallback to rules
    return _extract_with_rules(session_text)


def _extract_with_llm(session_text: str) -> List[Dict]:
    """用 LLM 提取结构化记忆"""
    import os
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("No OPENAI_API_KEY")

    from orgmind.config import OPENAI_BASE_URL, LLM_MODEL
    import openai
    client = openai.OpenAI(base_url=OPENAI_BASE_URL)

    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": LLM_PROMPT},
            {"role": "user", "content": session_text[:8000]},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=2000,
    )

    raw = resp.choices[0].message.content
    # Parse JSON
    data = json.loads(raw)
    # Handle both {"memories": [...]} and [...] formats
    if isinstance(data, dict):
        items = data.get("memories", data.get("items", []))
    else:
        items = data

    result = []
    for item in items:
        result.append({
            "type": item.get("type", "episodic"),
            "content": item.get("content", "")[:500],
            "confidence": float(item.get("confidence", 0.8)),
            "extracted_type": item.get("type", "decision"),
        })

    if not result:
        # LLM returned empty, fall through to rules
        raise RuntimeError("LLM returned no memories")

    return result


# === 规则提取 (降级) ===
DECISION_PATTERNS = [
    r'(?:决定|确认|采用|选择|敲定|定了|方案是|最终用)[^。！\n]{5,100}',
    r'(?:decided to|chose to|will use|going with|finalized)[^.!\n]{5,100}',
]
BUG_FIX_PATTERNS = [
    r'(?:报错|错误|bug|失败|崩溃|不工作|fix|fixed|resolved)[^。！\n]{5,100}',
    r'(?:修复|解决|改正|debug)[^。！\n]{5,100}',
]
BEST_PRACTICE_PATTERNS = [
    r'(?:最佳实践|建议|应该|必须|规范|原则|best practice|should always|must)[^。！\n]{5,100}',
]
ARCHITECTURE_PATTERNS = [
    r'(?:架构|技术栈|framework|stack|分层|模块|architecture)[^。！\n]{5,100}',
]

def _extract_with_rules(session_text: str) -> List[Dict]:
    """正则规则提取 (降级方案)"""
    results = []

    for patterns, mem_type in [
        (DECISION_PATTERNS, "decision"),
        (BUG_FIX_PATTERNS, "bug_fix"),
        (BEST_PRACTICE_PATTERNS, "best_practice"),
        (ARCHITECTURE_PATTERNS, "architecture"),
    ]:
        for pattern in patterns:
            matches = re.finditer(pattern, session_text, re.IGNORECASE)
            for m in matches:
                content = m.group(0).strip()
                if len(content) < 8:
                    continue
                results.append({
                    "type": mem_type,
                    "content": content[:500],
                    "confidence": 0.75,
                    "extracted_type": mem_type,
                })

    # 去重
    seen = set()
    deduped = []
    for r in results:
        key = r["content"][:50]
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    return deduped


def detect_repeated_pattern(memories: List[Dict]) -> Dict:
    """检测重复出现的模式"""
    from collections import Counter
    type_counts = Counter(m.get("extracted_type", m.get("type", "")) for m in memories)
    for ptype, count in type_counts.most_common(1):
        if count >= 3:
            return {
                "pattern_type": ptype,
                "count": count,
                "skill_name": f"auto-{ptype}-pattern",
                "skill_description": f"Auto-detected pattern: {ptype} appears {count} times",
                "confidence": min(0.5 + count * 0.1, 0.95),
            }
    return None


def generate_skill_draft(pattern: Dict) -> str:
    """生成 SKILL.md 草稿"""
    return f"""# {pattern["skill_name"]}

## Description
{pattern["skill_description"]}

## Pattern
Type: {pattern["pattern_type"]}
Occurrences: {pattern["count"]}
Confidence: {pattern["confidence"]:.0%}

## Status
[WARNING] Auto-generated draft, requires human review before publishing.
"""
