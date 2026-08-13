from __future__ import annotations
from .models import Claim, Contradiction, SignalEvidence
from .llm import LLMClient, ModelRole

SCAN_SCHEMA = {
    "type": "object",
    "properties": {
        "signals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "quote": {"type": "string"},
                    "confidence": {"type": "number"},
                },
            },
        },
        "contradictions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "a": {"type": "string"}, "b": {"type": "string"},
                    "nature": {"type": "string"},
                },
            },
        },
    },
}

CONFIRM_SCHEMA = {
    "type": "object",
    "properties": {
        "confirmations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"index": {"type": "integer"},
                               "confirmed": {"type": "boolean"},
                               "note": {"type": "string"}},
            },
        }
    },
}


def scrutinize(llm: LLMClient, answers: list[Claim],
               resume_claims: list[Claim]) -> tuple[list[SignalEvidence], list[Contradiction]]:
    scan_prompt = (
        "扫描以下回答与简历，初筛出：1) 虚构成分信号(AI味道)；2) 简历/回答间的技术、规模、时间线矛盾。"
        "宁可多报。\n\n回答:\n" +
        "\n".join(a.bullet for a in answers) +
        "\n\n简历断言:\n" + "\n".join(c.bullet for c in resume_claims)
    )
    scan = llm.structured(ModelRole.FLASH, scan_prompt, SCAN_SCHEMA)

    sig_candidates = scan.get("signals", [])
    contra_candidates = scan.get("contradictions", [])

    # 深挖：只对初筛命中项交给 Pro 逐条确认 —— 误报被驳回
    confirm_payload = [{"index": i, "sig": s.get("label"), "quote": s.get("quote", "")}
                       for i, s in enumerate(sig_candidates)]
    confirm = llm.structured(ModelRole.PRO, confirm_payload, CONFIRM_SCHEMA)

    confirmed_idx = {c["index"] for c in confirm.get("confirmations", [])
                     if c.get("confirmed")}

    signals: list[SignalEvidence] = []
    for i, s in enumerate(sig_candidates):
        if i in confirmed_idx and s.get("label"):
            signals.append(SignalEvidence(
                label=s["label"],
                quote=s.get("quote", ""),
                confidence=float(s.get("confidence", 1.0)),
                verdict_note=next((c.get("note", "") for c in confirm.get("confirmations", [])
                                   if c.get("index") == i), ""),
            ))
    # D 矛盾：本项目先用初筛原样透传（含 nature），不做二次确认，后续任务可加
    contradictions = [Contradiction(Claim(str(cc.get("a", "")), source="answer"),
                                    Claim(str(cc.get("b", "")), source="resume"),
                                    nature=str(cc.get("nature", "")))
                      for cc in contra_candidates if cc.get("a") and cc.get("b")]
    return signals, contradictions
