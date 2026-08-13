from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from .llm import LLMClient
from .machine import AdversarialStateMachine


def build_machine() -> AdversarialStateMachine | None:
    # 真实调用在此构造并返回已接好适配器(用户自备的 OpenAI 兼容适配器)的状态机；
    # 无配置时返回 None(CLI报错)。测试通过 monkeypatch 注入 MockLLM 后台的机器。
    return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="adverhire")
    sub = p.add_subparsers(dest="cmd", required=True)
    insp = sub.add_parser("inspect")
    insp.add_argument("resume", type=Path)
    insp.add_argument("-o", "--out", type=Path, default=None)
    insp.add_argument("--answers", type=Path, default=None)
    insp.add_argument("--to-stdout", action="store_true")
    args = p.parse_args(argv)

    if args.cmd == "inspect":
        machine = build_machine()
        if machine is None:
            print("未配置真实 LLM；请先注入适配器或使用 MockLLM 做冒烟。", file=sys.stderr)
            return 1
        text = args.resume.read_text(encoding="utf-8")
        claims, qs = machine.parse_then_probe(text)
        payload = {
            "questions": [{"question": t.question, "wrong_preset": t.wrong_preset,
                           "claim": t.claim.bullet, "discriminators": t.discriminators}
                          for t in qs.questions],
            "per_trap": qs.per_trap,
        }
        if args.answers and args.answers.exists():
            # 简版：读 rows 组成 answers 后走 advance
            payload["report"] = "review via API (answers injection is stub)"
        data = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.to_stdout or args.out is None:
            print(data)
        else:
            args.out.write_text(data, encoding="utf-8")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
