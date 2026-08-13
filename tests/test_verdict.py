from adverhire.verdict import build_report
from adverhire.llm import ModelRole, MockLLM
from adverhire.models import RiskLevel, SignalEvidence, Contradiction, Claim

SIG = SignalEvidence("no_embodied_detail", "用单机redis就够了", 0.8, "规模存疑")
CONTRA = Contradiction(Claim("a", source="answer"), Claim("b", source="resume"), "scale_mismatch")

def test_build_report_maps_overall_and_fills_dimensions():
    mock = MockLLM(responses={
        ModelRole.PRO: [
            {"overall": "MEDIUM", "by_dimension": {"no_embodied_detail": 0.8}},
            "多项无具身细节，技术规模存疑，建议面试官人工复核。",
        ],
    })
    rep = build_report(mock, [SIG], [CONTRA])
    assert rep.overall == RiskLevel.MEDIUM
    assert rep.by_dimension["no_embodied_detail"] == 0.8
    assert all(isinstance(d, float) for d in rep.by_dimension.values())  # 五维补齐

def test_never_emits_elimination_conclusion():
    mock = MockLLM(responses={
        ModelRole.PRO: [
            {"overall": "HIGH", "by_dimension": {}},
            "存在较多虚构成分。",
        ],
    })
    rep = build_report(mock, [SIG], [])
    # 不变量 #2：报告只含风险分级，绝无淘汰/录用字样
    text = (rep.summary + str(rep.overall)).lower()
    assert "淘汰" not in text and "录用" not in text
