from __future__ import annotations

from .models import (
    RiskLevel, SignalEvidence, Contradiction, RiskReport, Dimen,
)

# 各维度的风险权重。
# "AI 空泛胜任力"维度（模板化/泛化/无情绪）是 AI 代答最强的泄漏信号，满权重。
# "风格"维度（无具身/用词规整）真人才也会命中（简洁/精炼的回答），降权避免误伤。
_DIM_WEIGHT = {
    "template_cliche": 1.0,
    "over_generalization": 1.0,
    "missing_affect": 1.0,
    "no_embodied_detail": 0.5,
    "over_standardized": 0.25,
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
