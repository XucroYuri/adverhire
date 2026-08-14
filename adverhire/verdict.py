from __future__ import annotations

from .models import (
    RiskLevel, SignalEvidence, Contradiction, RiskReport, Dimen,
)

# 各维度风险权重。
# 结构化/行为信号（consistency_collapse/detail_exhaustion/idiosyncrasy_absence/
# behavioral_uniformity）是 AI 包装干扰下难伪造的核心信号，满权重。
# 缺失式五维（template/over_generalization/no_embodied/missing_affect/over_standardized）
# 可被聪明 AI 用真人口吻词+假数字模仿，降为低权重第一遍快筛，单条不足升档。
_DIM_WEIGHT = {
    # 结构性核心信号（高分）
    "consistency_collapse": 1.0,
    "detail_exhaustion": 1.0,
    "idiosyncrasy_absence": 1.0,
    "behavioral_uniformity": 1.0,
    # 缺失式五维（低分，可被模仿）
    "template_cliche": 0.4,
    "over_generalization": 0.5,
    "no_embodied_detail": 0.3,
    "missing_affect": 0.2,
    "over_standardized": 0.1,
}


def _by_dimension(signals: list[SignalEvidence]) -> dict[str, float]:
    dims: dict[str, float] = {}
    for d in Dimen:
        dims[d.value] = 0.0
    for s in signals:
        dims.setdefault(s.label, 0.0)
        dims[s.label] = max(dims[s.label], s.confidence)
    return dims


def _grade(dims: dict[str, float], contradictions: list[Contradiction]) -> RiskLevel:
    """纯规则计分：按维度加权，同一维度多答只取最高置信度（不因答得多而加重）。

    不变量 #2：返回值必然取自三值之一，结构性绝不产生淘汰/录用结论。
    """
    weighted = sum(_DIM_WEIGHT.get(dim, 0.25) * max(0.0, conf)
                   for dim, conf in dims.items())
    contra_weight = sum(1.0 for _ in contradictions)
    total = weighted + contra_weight
    if total >= 1.5:
        return RiskLevel.HIGH
    if total >= 0.7:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def grade_risk(signals: list[SignalEvidence], contradictions: list[Contradiction],
               summary: str = "") -> RiskReport:
    """确定性风险报告。summary 由调用方(subagent)注入，引擎不生成文本结论。"""
    dims = _by_dimension(signals)
    return RiskReport(
        overall=_grade(dims, contradictions),
        signals=signals,
        contradictions=contradictions,
        by_dimension=dims,
        summary=summary,
    )
