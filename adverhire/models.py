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
