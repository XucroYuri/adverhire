"""薄驱动脚本：接对抗审查引擎，供 Agent Skill 调用。

用法：
    python scripts/verify.py probe  <resume.md> [--mock] [-o out.json]
    python scripts/verify.py review <resume.md> <answers.json> [--mock] [-o out.json]

--mock：用 MockLLM 跑全流程（确定性，无网络/密钥），用于测试与验证。
不带 --mock：读 API_KEY / BASE_URL / PRO_MODEL / FLASH_MODEL 环境变量走 OpenAI 兼容接口。

引擎（adverhire/*）零改动；本脚本只负责 argv 解析 + 装配 + 序列化。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# 使本脚本可直接运行（scripts/ 目录不是包根）：把仓库根加入 import 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adverhire.machine import AdversarialStateMachine
from adverhire.models import Claim
from adverhire.llm import LLMClient, ModelRole, MockLLM

API_KEY = os.environ.get("API_KEY") or "sk-xxx"
BASE = os.environ.get("BASE_URL", "https://api.deepseek.com/v1/chat/completions")
PRO_MODEL = os.environ.get("PRO_MODEL", "deepseek-chat")     # 占位，需按官方文档核对
FLASH_MODEL = os.environ.get("FLASH_MODEL", "deepseek-chat")  # 占位，需按官方文档核对


class OpenAIClient(LLMClient):
    """真实模型适配器（用户自备凭证；复用冒烟脚本同一模式）。"""

    def _chat(self, role, prompt):
        import requests

        r = requests.post(
            BASE,
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": PRO_MODEL if role is ModelRole.PRO else FLASH_MODEL,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def generate(self, role, prompt):
        return self._chat(role, prompt)

    def structured(self, role, prompt, schema):
        out = self._chat(role, prompt + f"\n请仅输出 JSON：{json.dumps(schema)}")
        return json.loads(out)


def build_machine(mock: bool, responses: dict | None = None) -> AdversarialStateMachine:
    if not mock:
        return AdversarialStateMachine(OpenAIClient())
    # --mock 模式：无 responses 时仅验证管线装配（引擎调用会因空队列报错，属预期）
    llm: LLMClient = MockLLM(responses or {})
    return AdversarialStateMachine(llm)


def _claim_bullets(claims: list[Claim]) -> list[dict]:
    return [
        {
            "bullet": c.bullet,
            "tech": c.tech,
            "metric": c.metric,
            "source": c.source,
        }
        for c in claims
    ]


def _report_json(report) -> dict:
    return {
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


def _emit(payload: dict, out: Path | None):
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    if out is None:
        print(data)
    else:
        out.write_text(data, encoding="utf-8")


def _load_responses(path: Path | None) -> dict | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_probe(args) -> int:
    machine = build_machine(args.mock, _load_responses(args.responses))
    text = args.resume.read_text(encoding="utf-8")
    claims, qs = machine.parse_then_probe(text)
    payload = {
        "claims": _claim_bullets(claims),
        "questions": [
            {
                "question": t.question,
                "wrong_preset": t.wrong_preset,
                "claim": t.claim.bullet,
                "claim_idx": _find_index(claims, t.claim),
                "discriminators": t.discriminators,
            }
            for t in qs.questions
        ],
        "per_trap": qs.per_trap,
    }
    _emit(payload, args.out)
    return 0


def cmd_review(args) -> int:
    machine = build_machine(args.mock, _load_responses(args.responses))
    resume_text = args.resume.read_text(encoding="utf-8")
    answers_raw = json.loads(args.answers.read_text(encoding="utf-8"))
    answers = [Claim(str(a), source="answer") for a in answers_raw]

    claims, qs = machine.parse_then_probe(resume_text)
    report = machine.advance(answers, claims)

    payload = {
        "claims": _claim_bullets(claims),
        "questions": [t.question for t in qs.questions],
        "answers": [a.bullet for a in answers],
        "report": _report_json(report),
    }
    _emit(payload, args.out)
    return 0


def _find_index(claims: list[Claim], target: Claim) -> int | None:
    for i, c in enumerate(claims):
        if c.bullet == target.bullet:
            return i
    return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="adverhire-verify")
    sub = p.add_subparsers(dest="cmd", required=True)

    probe_p = sub.add_parser("probe")
    probe_p.add_argument("resume", type=Path)
    probe_p.add_argument("--mock", action="store_true")
    probe_p.add_argument("--responses", type=Path, default=None,
                         help="--mock 时使用的 MockLLM 响应文件(JSON dict)")
    probe_p.add_argument("-o", "--out", type=Path, default=None)

    review_p = sub.add_parser("review")
    review_p.add_argument("resume", type=Path)
    review_p.add_argument("answers", type=Path)
    review_p.add_argument("--mock", action="store_true")
    review_p.add_argument("--responses", type=Path, default=None,
                          help="--mock 时使用的 MockLLM 响应文件(JSON dict)")
    review_p.add_argument("-o", "--out", type=Path, default=None)

    args = p.parse_args(argv)

    if args.cmd == "probe":
        return cmd_probe(args)
    if args.cmd == "review":
        return cmd_review(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
