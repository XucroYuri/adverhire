from __future__ import annotations

from .models import Claim, ImpactedTrap, QuestionSet, TrapTactic


def is_claimable(claim: Claim) -> bool:
    """断言可验证：有量化指标或有技术栈。"""
    return claim.metric is not None or bool(claim.tech)


def trap_tactics(claims: list[Claim]) -> list[TrapTactic]:
    """确定性产出每个可验证断言可用的坑题战术，供 subagent 依此设计具体坑题。

    - A1 数值：断言有量化指标 → 植入错误但合理的数值，看是否纠正。
    - A2 技术细节：断言有技术栈 → 把实现细节改成"看似合理但实际错"，看是否指出。
    - A3 决策：断言涉及设计/选型取向 → 植入"外行才会做"的决策，看是否反驳。

    具体 wrong_preset / question / discriminators 的语义内容由 subagent 依战术实时设计。
    """
    tactics: list[TrapTactic] = []
    for claim in claims:
        if not is_claimable(claim):
            continue
        if claim.metric is not None:
            tactics.append(TrapTactic(
                kind="a1_numeric", claim=claim,
                angle="把断言里的量化指标改成错误但合理的新值，请候选人确认或纠正。",
                focus="量化指标",
            ))
        if claim.tech:
            tactics.append(TrapTactic(
                kind="a2_technical", claim=claim,
                angle="把实现细节/技术选型改成看似合理但实际错的表述，看候选人是否指出。",
                focus="技术细节",
            ))
        if "选型" in claim.bullet or "架构" in claim.bullet or "设计" in claim.bullet \
                or "技术方案" in claim.bullet or "主导" in claim.bullet:
            tactics.append(TrapTactic(
                kind="a3_decision", claim=claim,
                angle="植入一个外行才会选的决策，看候选人是否解释权衡。",
                focus="决策取舍",
            ))
    return tactics


def validate_traps(claims: list[Claim], raw_traps: list[dict]) -> QuestionSet:
    """校验 subagent 填的坑题，强制不变量 #1：

    坑题永远派生自真实、可验证的断言——只保留 claim_idx 在可 claimable 范围内、
    且 question 非空的项。语义内容由 subagent 提供，这里只做确定性下限校验。
    """
    claimable_idx = {i for i, c in enumerate(claims) if is_claimable(c)}
    traps: list[ImpactedTrap] = []
    for item in raw_traps or []:
        idx = item.get("claim_idx")
        question = str(item.get("question") or "").strip()
        # 不变量 #1：idx 必须落在可 claimable 断言上，且问题非空
        if not (isinstance(idx, int) and idx in claimable_idx and question):
            continue
        traps.append(ImpactedTrap(
            claim=claims[idx],
            wrong_preset=str(item.get("wrong_preset") or "").strip(),
            question=question,
            discriminators=[str(d) for d in item.get("discriminators", []) if d],
        ))
    return QuestionSet(questions=traps)
