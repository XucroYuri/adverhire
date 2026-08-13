from __future__ import annotations

from .models import Claim, QuestionSet, RiskReport, TrapTactic
from .parse import normalize_claims
from .probe import trap_tactics, validate_traps
from .scrutinize import detect_signals, detect_contradictions
from .verdict import grade_risk


class AdversarialStateMachine:
    """对抗审查状态机的纯函数组合（无 LLM 依赖）。

    subagent 作为推理主体，按步骤调用本职工具；本类负责确定性数据/规则部分：
    - parse_and_tactics：subagent 已提 raw claims → 归一化 → 坑题战术
    - validate(subagent 设计坑题后)：校验不变量 #1
    - advance：detect_signals + detect_contradictions → grade_risk
    """

    def parse_and_tactics(self, raw_claims: list[dict]) -> tuple[list[Claim], list[TrapTactic]]:
        claims = normalize_claims(raw_claims)
        tactics = trap_tactics(claims)
        return claims, tactics

    def validate(self, claims: list[Claim], raw_traps: list[dict]) -> QuestionSet:
        return validate_traps(claims, raw_traps)

    def advance(self, answers: list[Claim], resume_claims: list[Claim],
                summary: str = "") -> RiskReport:
        signals = detect_signals(answers)
        contradictions = detect_contradictions(resume_claims, answers)
        return grade_risk(signals, contradictions, summary=summary)
