from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class Dimen(str, Enum):
    TEMPLATE_CLICHE = "template_cliche"
    NO_EMBODIED_DETAIL = "no_embodied_detail"
    OVER_GENERALIZATION = "over_generalization"
    MISSING_AFFECT = "missing_affect"
    OVER_STANDARDIZED = "over_standardized"

@dataclass
class Claim:
    bullet: str
    tech: list[str] = field(default_factory=list)
    metric: float | None = None
    source: str = "resume"  # "resume" | "answer"

@dataclass
class ImpactedTrap:
    claim: Claim
    wrong_preset: str
    question: str
    discriminators: list[str] = field(default_factory=list)

@dataclass
class TrapTactic:
    kind: str          # "a1_numeric" / "a2_technical" / "a3_decision"
    claim: Claim
    angle: str         # 战术提示：subagent 依此设计具体坑题
    focus: str         # 应从哪个细节切入（如 metric / 某技术 / 某决策）

@dataclass
class FollowUp:
    ancestor_question: str
    branch: str  # vague / corrected / echoed
    question: str
    depth: int
    discriminator_hit: bool = False

@dataclass
class QuestionSet:
    questions: list[ImpactedTrap] = field(default_factory=list)
    per_trap: dict[str, list[FollowUp]] = field(default_factory=dict)

@dataclass
class Contradiction:
    a: Claim
    b: Claim
    nature: str  # tech_mismatch / scale_mismatch / timeline_conflict / procedural_contradiction

@dataclass
class SignalEvidence:
    label: str
    quote: str
    confidence: float = 1.0
    verdict_note: str = ""

@dataclass
class RiskReport:
    overall: RiskLevel
    signals: list[SignalEvidence] = field(default_factory=list)
    contradictions: list[Contradiction] = field(default_factory=list)
    by_dimension: dict[str, float] = field(default_factory=dict)
    summary: str = ""


@dataclass
class AnswerTurn:
    """一轮问答的行为记录。除 text 外都是 subagent 在会话中观察记录的行为字段。

    depth: 对同一断言的第几层追问(0=首答)
    answer_latency: 回答前思考时长(秒)的主观档位或秒数(0=未知/秒答)
    self_repaired: 是否有真实自我修正("其实不对""我说错了""重新说"等纠错轨迹)
    affect_cue: 是否带真实情绪起伏(懊悔/得意/卡壳/挣扎)
    reasoning_visible: 是否愿意露出推理过程(给过程而非只下结论)
    """
    text: str
    depth: int = 0
    answer_latency: float | None = None   # None=未观察；0≈秒答
    self_repaired: bool = False
    affect_cue: bool = False
    reasoning_visible: bool = False
