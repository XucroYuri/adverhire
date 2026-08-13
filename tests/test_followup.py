from adverhire.followup import classify_answer, followup_directive
from adverhire.models import ImpactedTrap, Claim

TRAP = ImpactedTrap(Claim("优化缓存 QPS+50%", ["redis"], 50.0, "resume"),
                    wrong_preset="改成1800", question="从200怎么调到1800的？",
                    discriminators=["纠正", "其实", "回滚", "踩"])


def test_classify_corrected_hits_discriminator():
    assert classify_answer("其实不是，改成的是1200，我们踩过这个坑", TRAP) == "corrected"


def test_classify_vague_when_short_or_forgetful():
    assert classify_answer("嗯" * 3, TRAP) == "vague"
    assert classify_answer("记不清那段细节了", TRAP) == "vague"


def test_classify_defaults_to_echoed():
    assert classify_answer("反正我们做了深度优化和最佳实践，显著提升整体性能", TRAP) == "echoed"


def test_followup_directive_corrected_terminates():
    d = followup_directive("corrected", TRAP)
    assert "终止" in d  # corrected → 本题终止


def test_followup_directive_vague_asks_for_detail():
    d = followup_directive("vague", TRAP)
    assert "代码" in d or "数字" in d or "取舍" in d


def test_followup_directive_echoed_pushes_on_before_state():
    d = followup_directive("echoed", TRAP)
    assert "改之前" in d or "线上" in d or "发生了什么" in d
