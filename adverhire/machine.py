from __future__ import annotations
from .models import Claim, QuestionSet, RiskReport
from .llm import LLMClient
from .parse import parse_resume
from .probe import gen_traps
from .scrutinize import scrutinize
from .verdict import build_report


class AdversarialStateMachine:
    """对抗审查状态机：parse -> probe -> (问答) -> scrutinize -> verdict。"""

    def __init__(self, llm: LLMClient):
        self._llm = llm

    def parse_then_probe(self, text: str) -> tuple[list[Claim], QuestionSet]:
        claims = parse_resume(self._llm, text)
        qs = gen_traps(self._llm, claims)
        return claims, qs

    def advance(self, answers: list[Claim], resume_claims: list[Claim]) -> RiskReport:
        signals, contradictions = scrutinize(self._llm, answers, resume_claims)
        return build_report(self._llm, signals, contradictions)
