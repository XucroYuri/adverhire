"""冒烟运行器：对 R1 夹具真实跑一份 RiskReport。用法：
   API_KEY=... BASE_URL=... python scripts/run_with_real_llm.py
依赖：用户当前仓库无 API SDK；此处用 requests 直连 OpenAI 兼容接口。"""
import json, os
from pathlib import Path
import requests
from adverhire.models import Claim
from adverhire.llm import LLMClient, ModelRole
from adverhire.machine import AdversarialStateMachine

API_KEY = os.environ.get("API_KEY") or "sk-xxx"
BASE = os.environ.get("BASE_URL", "https://api.deepseek.com/v1/chat/completions")
PRO = os.environ.get("PRO_MODEL", "deepseek-chat")   # 占位，需按官方文档核对
FLASH = os.environ.get("FLASH_MODEL", "deepseek-chat")


class OpenAIClient(LLMClient):
    def _chat(self, role, prompt):
        r = requests.post(BASE, headers={"Authorization": f"Bearer {API_KEY}"},
                          json={"model": PRO if role is ModelRole.PRO else FLASH,
                                "messages": [{"role": "user", "content": prompt}]}, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def generate(self, role, prompt): return self._chat(role, prompt)
    def structured(self, role, prompt, schema):
        out = self._chat(role, prompt + f"\n请仅输出 JSON：{json.dumps(schema)}")
        return json.loads(out)


def main():
    here = Path(__file__).parent.parent
    for name in ("real", "faked"):
        md = (here / f"tests/fixtures/{name}.md").read_text(encoding="utf-8")
        ans = json.loads((here / f"tests/fixtures/{name}_answers.json").read_text(encoding="utf-8"))
        sm = AdversarialStateMachine(OpenAIClient())
        claims, qs = sm.parse_then_probe(md)
        answers = [Claim(a, source="answer") for a in ans]
        report = sm.advance(answers, claims)
        print(f"=== {name} ===")
        print(f"overall: {report.overall.value}")
        print("signals:", [s.label for s in report.signals])
        print("contradictions:", [c.nature for c in report.contradictions])
        print("by_dimension:", report.by_dimension)
        print("summary:", report.summary)


if __name__ == "__main__":
    main()
