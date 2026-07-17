"""
数据质量打分 - 对应 IMPLEMENTATION_SPEC 1.6
精确公式, 不是"AI判断质量好坏"
"""
from dataclasses import dataclass


@dataclass
class QualityInput:
    completeness: float      # 必填字段填充比例, 0~1
    schema_valid: float      # 通过校验记为1, 否则0
    near_duplicate_count: int
    source_trust: float      # 查信任表

SOURCE_TRUST = {
    "human_verified": 1.0,
    "agent_verified": 0.8,
    "agent_unverified": 0.5,
    "batch_import": 0.6,
}


def compute_quality_score(inp: QualityInput) -> float:
    """
    quality_score = 0.3*completeness + 0.2*valid + 0.2*(1-duplicate_penalty) + 0.3*source_trust
    """
    duplicate_penalty = min(1.0, inp.near_duplicate_count / 3)
    score = (
        0.3 * inp.completeness
        + 0.2 * inp.schema_valid
        + 0.2 * (1.0 - duplicate_penalty)
        + 0.3 * inp.source_trust
    )
    return round(score, 4)
