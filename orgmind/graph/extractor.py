"""
轻量实体抽取器 - 对应 DESIGN.md 4.6
规则优先, 仅对复杂实体调用 LLM
"""
import re
from typing import List, Dict, Tuple
from orgmind.graph.engine import get_graph_engine


def extract_entities_from_text(text: str) -> List[Tuple[str, str]]:
    """
    轻量实体抽取: 基于规则的命名实体提取。
    返回 [(实体名, 实体类型), ...]。
    """
    entities = []

    # 中国大陆手机号 → Person (脱敏处理)
    phone_matches = re.findall(r"1[3-9]\d{9}", text)
    for m in phone_matches:
        entities.append((m[:3] + "****" + m[-4:], "Person"))

    # 邮箱 → Person
    email_matches = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    for m in email_matches:
        entities.append((m, "Person"))

    # "XX决定/采用/确认了YY" → Decision
    decision_matches = re.findall(r"(决定|采用|确认)[：:\s]*([^\s，。,\.]{2,20})", text)
    for _, decision in decision_matches:
        entities.append((decision, "Decision"))

    # "XX项目" → Project
    project_matches = re.findall(r"([^\s]{2,10})(?:项目|系统|平台|模块)", text)
    for m in project_matches:
        entities.append((m, "Project"))

    return entities


def build_graph_from_text(
    org_id: str, text: str, source_id: str, source_type: str = "memory"
) -> None:
    """
    从文本抽取实体/关系, 增量写入图引擎。
    不做全量重建，只对增量做局部写入。
    """
    engine = get_graph_engine()
    entities = extract_entities_from_text(text)

    for name, etype in entities:
        engine.add_node(name, etype, org_id)

    # 关联 Source → Entity (MENTIONED_IN)
    for name, etype in entities:
        engine.add_edge(source_id[:20], name, org_id, "MENTIONED_IN")
