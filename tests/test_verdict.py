from adverhire.verdict import grade_risk
from adverhire.models import SignalEvidence, Claim, Contradiction, RiskLevel


def sig(label: str, conf: float = 0.8, quote: str = "原文"):
    return SignalEvidence(label=label, quote=quote, confidence=conf)


def contra():
    return Contradiction(Claim("a", source="answer"), Claim("b", source="resume"), "scale_mismatch")


def test_grade_low_when_few_weak_signals():
    rep = grade_risk([sig("no_embodied_detail", 0.3)], [])
    assert rep.overall == RiskLevel.LOW


def test_grade_medium_requires_strong_competence_signal():
    # 单个满分权重维度(template_cliche)的强信号 → MEDIUM
    rep = grade_risk([sig("template_cliche", 0.8)], [])
    assert rep.overall == RiskLevel.MEDIUM


def test_grade_low_with_only_downweighted_style_signal():
    # no_embodied_detail 是降权维度(0.5)，单个即使 0.8 也到不了 MEDIUM(0.8*0.5=0.4<0.7)
    rep = grade_risk([sig("no_embodied_detail", 0.8)], [])
    assert rep.overall == RiskLevel.LOW


def test_grade_high_with_many_signals_and_contra():
    rep = grade_risk(
        [sig("no_embodied_detail", 0.8), sig("over_generalization", 0.7)],
        [contra()],
    )
    assert rep.overall == RiskLevel.HIGH


def test_by_dimension_all_five_present_and_float():
    rep = grade_risk([sig("no_embodied_detail", 0.8)], [])
    dims = rep.by_dimension
    assert set(dims) == {"template_cliche", "no_embodied_detail", "over_generalization",
                         "missing_affect", "over_standardized"}
    assert all(isinstance(v, float) for v in dims.values())


def test_invariant2_never_emits_elimination_conclusion():
    # overall 只可能取三值之一，绝不产生淘汰/录用
    for sigs, contras in (([sig("no_embodied_detail", 0.9)], [contra()]),
                          ([], []),
                          ([sig("x", 0.5), sig("y", 0.5), sig("z", 0.5), sig("w", 0.5)], [])):
        rep = grade_risk(sigs, contras, summary="供参考")
        assert rep.overall in {RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH}
        text = (rep.summary + str(rep.overall)).lower()
        assert "淘汰" not in text and "录用" not in text
