from __future__ import annotations

import math

from .models import Claim


def _to_float(value) -> float | None:
    if value in (None, "", "null"):
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return f


def normalize_claims(raw: list[dict]) -> list[Claim]:
    """把 subagent/调用方已提取的 raw claims 归一化成 Claim。

    输入：`[{bullet, tech, metric, source}]`。`metric` 可为 str/int/float/None；
    `source` 缺省 "resume"。非有限数值(inf/nan)/非法值置 None。
    纯函数，零 LLM 依赖。
    """
    claims: list[Claim] = []
    for item in raw or []:
        source = str(item.get("source", "resume") or "resume")
        claims.append(Claim(
            bullet=str(item.get("bullet", "")),
            tech=[str(t) for t in item.get("tech", []) if t],
            metric=_to_float(item.get("metric")),
            source=source,
        ))
    return claims
