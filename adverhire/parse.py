from __future__ import annotations
from .models import Claim
from .llm import LLMClient, ModelRole

RESUME_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "bullet": {"type": "string"},
                    "tech": {"type": "array", "items": {"type": "string"}},
                    "metric": {"type": ["string", "null"]},
                    "source": {"type": "string"},
                },
            },
        }
    },
}


def _to_float(value) -> float | None:
    if value in (None, "", "null"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_resume(llm: LLMClient, text: str) -> list[Claim]:
    data = llm.structured(ModelRole.FLASH, text, RESUME_SCHEMA)
    claims = []
    for item in data.get("claims", []):
        claims.append(Claim(
            bullet=str(item.get("bullet", "")),
            tech=[str(t) for t in item.get("tech", []) if t],
            metric=_to_float(item.get("metric")),
            source=str(item.get("source", "resume")) or "resume",
        ))
    return claims
