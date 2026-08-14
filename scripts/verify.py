"""薄驱动脚本：subagent 与确定性规则内核之间的结构化接口。零 LLM 依赖。

用法（subagent / CLI 调用）：
    python scripts/verify.py tactics  --claims claims.json [-o out]
        subagent 已用自身推理把简历抽成 raw claims JSON
        → 引擎归一化 + 输出坑题战术(tactics)，subagent 依此实时设计具体坑题
    python scripts/verify.py validate --claims claims.json --traps traps.json [-o out]
        subagent 填好坑题后 → 引擎强制不变量#1(坑题派生自真实可验证断言、非空)
        → 输出 QuestionSet
    python scripts/verify.py review   --claims claims.json --answers answers.json [--summary "..."] [-o out]
        subagent 收集全部回答后 → detect_signals + detect_contradictions + grade_risk
        → 输出 RiskReport（summary 可由 subagent 注入一句话）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adverhire.machine import AdversarialStateMachine
from adverhire.models import Claim

SM = AdversarialStateMachine()


def _emit(payload: dict, out: Path | None):
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    if out is None:
        print(data)
    else:
        out.write_text(data, encoding="utf-8")


def cmd_tactics(args) -> int:
    raw = json.loads(args.claims.read_text(encoding="utf-8"))
    claims, tactics = SM.parse_and_tactics(raw)
    payload = {
        "claims": [
            {"bullet": c.bullet, "tech": c.tech, "metric": c.metric, "idx": i}
            for i, c in enumerate(claims)
        ],
        "tactics": [
            {"claim_idx": _idx_of(claims, t.claim), "kind": t.kind,
             "angle": t.angle, "focus": t.focus}
            for t in tactics
        ],
    }
    _emit(payload, args.out)
    return 0


def cmd_validate(args) -> int:
    raw_claims = json.loads(args.claims.read_text(encoding="utf-8"))
    raw_traps = json.loads(args.traps.read_text(encoding="utf-8"))
    claims, _ = SM.parse_and_tactics(raw_claims)
    qs = SM.validate(claims, raw_traps)
    payload = {
        "questions": [
            {"question": t.question, "wrong_preset": t.wrong_preset,
             "claim": t.claim.bullet, "discriminators": t.discriminators,
             "claim_idx": _idx_of(claims, t.claim)}
            for t in qs.questions
        ],
        "per_trap": qs.per_trap,
    }
    _emit(payload, args.out)
    return 0


def cmd_review(args) -> int:
    raw_claims = json.loads(args.claims.read_text(encoding="utf-8"))
    answers_raw = json.loads(args.answers.read_text(encoding="utf-8"))
    claims, _ = SM.parse_and_tactics(raw_claims)
    # answers 支持两种形态：
    #   ["回答文本", ...]（纯文本）                                         → Claim
    #   [{"text": "...", "depth":1, "self_repaired":true, ...}, ...]（含行为） → AnswerTurn
    from adverhire.models import AnswerTurn
    answers = []
    for item in answers_raw:
        if isinstance(item, str):
            answers.append(Claim(item, source="answer"))
        else:
            answers.append(AnswerTurn(
                text=str(item.get("text", "")),
                depth=int(item.get("depth", 0)),
                answer_latency=(float(item["answer_latency"])
                                if item.get("answer_latency") is not None else None),
                self_repaired=bool(item.get("self_repaired", False)),
                affect_cue=bool(item.get("affect_cue", False)),
                reasoning_visible=bool(item.get("reasoning_visible", False)),
            ))
    report = SM.advance(answers, claims, summary=args.summary or "")
    payload = {
        "overall": report.overall.value,
        "signals": [
            {"label": s.label, "quote": s.quote, "confidence": s.confidence,
             "verdict_note": s.verdict_note}
            for s in report.signals
        ],
        "contradictions": [
            {"nature": c.nature, "a": c.a.bullet, "b": c.b.bullet}
            for c in report.contradictions
        ],
        "by_dimension": report.by_dimension,
        "summary": report.summary,
    }
    _emit(payload, args.out)
    return 0


def _idx_of(claims: list[Claim], target: Claim) -> int | None:
    for i, c in enumerate(claims):
        if c.bullet == target.bullet:
            return i
    return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="adverhire-verify")
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("tactics")
    t.add_argument("--claims", required=True, type=Path)
    t.add_argument("-o", "--out", type=Path, default=None)

    v = sub.add_parser("validate")
    v.add_argument("--claims", required=True, type=Path)
    v.add_argument("--traps", required=True, type=Path)
    v.add_argument("-o", "--out", type=Path, default=None)

    r = sub.add_parser("review")
    r.add_argument("--claims", required=True, type=Path)
    r.add_argument("--answers", required=True, type=Path)
    r.add_argument("--summary", type=str, default="")
    r.add_argument("-o", "--out", type=Path, default=None)

    args = p.parse_args(argv)
    if args.cmd == "tactics":
        return cmd_tactics(args)
    if args.cmd == "validate":
        return cmd_validate(args)
    if args.cmd == "review":
        return cmd_review(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
