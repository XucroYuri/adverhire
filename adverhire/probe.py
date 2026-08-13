from __future__ import annotations
from .models import Claim, ImpactedTrap, QuestionSet
from .llm import LLMClient, ModelRole

TRAP_SCHEMA = {
    "type": "object",
    "properties": {
        "traps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_idx": {"type": "integer"},
                    "wrong_preset": {"type": "string"},
                    "question": {"type": "string"},
                    "discriminators": {"type": "array", "items": {"type": "string"}},
                },
            },
        }
    },
}


def gen_traps(llm: LLMClient, claims: list[Claim]) -> QuestionSet:
    # 只对"可验证断言"生成坑题：有量化指标或技术栈
    claimable = [i for i, c in enumerate(claims) if c.metric is not None or c.tech]
    if not claimable:
        return QuestionSet()

    prompt = _prompt_for(claims, claimable)
    data = llm.structured(ModelRole.PRO, prompt, TRAP_SCHEMA)

    traps: list[ImpactedTrap] = []
    for item in data.get("traps", []):
        idx = item.get("claim_idx")
        question = (item.get("question") or "").strip()
        if isinstance(idx, int) and 0 <= idx < len(claims) and question:
            traps.append(ImpactedTrap(
                claim=claims[idx],
                wrong_preset=(item.get("wrong_preset") or "").strip(),
                question=question,
                discriminators=[str(d) for d in item.get("discriminators", []) if d],
            ))
    # 不变量 #1：只保留能关联到既有 Claim 的坑题（上面已过滤越界 idx）
    return QuestionSet(questions=traps)


def _prompt_for(claims: list[Claim], claimable: list[int]) -> str:
    preview = "\n".join(f"[{i}] {claims[i].bullet}" for i in claimable)
    return (
        "对抗性坑题生成。对下列简历断言，为每条生成一个\"看似合理但错误\"的验证坑题：\n"
        f"{preview}\n要求：坑题必须派生自该断言本身，不提出格问题。"
    )
