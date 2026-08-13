from __future__ import annotations
from .models import ImpactedTrap, FollowUp
from .llm import LLMClient, ModelRole


def classify_answer(text: str, trap: ImpactedTrap) -> str:
    t = (text or "").strip()
    if any(seg in t for seg in trap.discriminators):
        return "corrected"
    if len(t) < 20 or any(k in t for k in ("记不清", "忘了", "一时半会儿", "举例")):
        return "vague"
    return "echoed"


PROMPT_TMPL = (
    "候选人对坑题「{question}」的回答是：\n{answer}\n"
    "这是第 {depth} 层追问。若回答含糊不清，追问具体代码/数字/当时取舍；"
    "若顺杆爬复读，追问改之前的线上情况。只输出一句追问。"
)


def next_followup(llm: LLMClient, trap: ImpactedTrap, answer: str, depth: int) -> FollowUp:
    branch = classify_answer(answer, trap)
    prompt = PROMPT_TMPL.format(question=trap.question, answer=answer, depth=depth)
    question = llm.generate(ModelRole.PRO, prompt).strip()
    return FollowUp(
        ancestor_question=trap.question,
        branch=branch,
        question=question,
        depth=depth + 1,
        discriminator_hit=(branch == "corrected"),
    )
