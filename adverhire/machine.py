from __future__ import annotations

from .models import AnswerTurn, Claim, QuestionSet, RiskReport, TrapTactic
from .parse import normalize_claims
from .probe import trap_tactics, validate_traps
from .scrutinize import (
    detect_signals, detect_contradictions,
    detect_structural, detect_behavioral,
)
from .verdict import grade_risk


def _as_turns(answers) -> list[AnswerTurn]:
    """兼容 list[Claim] 与 list[AnswerTurn]：统一成 AnswerTurn（行为字段缺省 False）。"""
    turns: list[AnswerTurn] = []
    for a in answers:
        if isinstance(a, AnswerTurn):
            turns.append(a)
        elif isinstance(a, Claim):
            turns.append(AnswerTurn(text=a.bullet, depth=0))
        else:
            turns.append(AnswerTurn(text=str(a), depth=0))
    return turns


class AdversarialStateMachine:
    """对抗审查状态机的纯函数组合（无 LLM 依赖）。

    subagent 作为推理主体，按步骤调用本职工具；本类负责确定性数据/规则部分：
    - parse_and_tactics：subagent 已提 raw claims → 归一化 → 坑题战术
    - validate(subagent 设计坑题后)：校验不变量 #1
    - advance：detect_signals + detect_structural + detect_behavioral +
               detect_contradictions → grade_risk

    answers 接受 list[AnswerTurn]（新，含行为字段）或 list[Claim]（兼容）。
    """

    def parse_and_tactics(self, raw_claims: list[dict]) -> tuple[list[Claim], list[TrapTactic]]:
        claims = normalize_claims(raw_claims)
        tactics = trap_tactics(claims)
        return claims, tactics

    def validate(self, claims: list[Claim], raw_traps: list[dict]) -> QuestionSet:
        return validate_traps(claims, raw_traps)

    def advance(self, answers, resume_claims: list[Claim],
                summary: str = "") -> RiskReport:
        turns = _as_turns(answers)
        signals = detect_signals([Claim(t.text, source="answer") for t in turns])
        signals += detect_structural(turns)
        signals += detect_behavioral(turns)
        contradictions = detect_contradictions(resume_claims,
                                               [Claim(t.text, source="answer") for t in turns])
        return grade_risk(signals, contradictions, summary=summary)
