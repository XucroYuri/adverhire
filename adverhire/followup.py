from __future__ import annotations

from .models import ImpactedTrap


def classify_answer(text: str, trap: ImpactedTrap) -> str:
    """纯规则判定回答三态：corrected / vague / echoed。

    - corrected：回答命中任一 discriminator（纠正了坑题错误预设 / 具身细节）。
    - vague：回答过短或明确表示记不清/忘记。
    - echoed：兜底，视为顺杆爬复读。
    """
    t = (text or "").strip()
    if any(seg in t for seg in trap.discriminators):
        return "corrected"
    if len(t) < 20 or any(k in t for k in ("记不清", "忘了", "一时半会儿", "举例")):
        return "vague"
    return "echoed"


def followup_directive(branch: str, trap: ImpactedTrap) -> str:
    """确定性的追问纪律：给定回答三态，返回该往哪个方向追问。

    返回的是"追问方向"而非具体问句——具体措辞由 subagent 依此纪律实时写出。
    """
    if branch == "corrected":
        return "已命中强判别信号（纠正了错误预设/具身细节）——此题即刻终止，视为真才信号。"
    if branch == "vague":
        return "回答含糊/记不清——追问一层具体到代码、数字、当时的取舍："
        f"让候选人回到「{trap.claim.bullet}」的实际做法。"
    return (f"回答顺杆爬/复读泛化——追问改之前的线上实际发生了什么，"
            f"落到「{trap.claim.bullet}」这个具体断言上。")
