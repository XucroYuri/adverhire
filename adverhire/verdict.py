from __future__ import annotations
from .models import RiskLevel, SignalEvidence, Contradiction, RiskReport, Dimen
from .llm import LLMClient, ModelRole

OVERALL_SCHEMA = {
    "type": "object",
    "properties": {
        "overall": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
        "by_dimension": {"type": "object"},
    },
}


def _risk(value: str) -> RiskLevel:
    try:
        return RiskLevel(value)
    except ValueError:
        return RiskLevel.LOW  # 非法值回落 LOW —— 不变量 #2（绝不升级成结论）


def build_report(llm: LLMClient, signals: list[SignalEvidence], contradictions: list[Contradiction],
                 summary_prompt: str = "用一句话给面试官的真实性参考") -> RiskReport:
    evidence = "\n".join(f"[{s.label}] {s.quote}" for s in signals)
    contra = "\n".join(f"{c.nature}: {c.a.bullet} vs {c.b.bullet}" for c in contradictions)
    judge = llm.structured(ModelRole.PRO, evidence + "\n" + contra, OVERALL_SCHEMA)

    dims: dict[str, float] = {}
    raw_dims = judge.get("by_dimension", {}) or {}
    for d in Dimen:
        try:
            dims[d.value] = float(raw_dims.get(d.value, 0.0))
        except (TypeError, ValueError):
            dims[d.value] = 0.0

    summary = llm.generate(ModelRole.PRO, summary_prompt + "\n" + evidence).strip()
    return RiskReport(
        overall=_risk(str(judge.get("overall", "LOW"))),
        signals=signals,
        contradictions=contradictions,
        by_dimension=dims,
        summary=summary,
    )
