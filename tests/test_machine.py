from adverhire.machine import AdversarialStateMachine
from adverhire.llm import ModelRole, MockLLM
from adverhire.models import RiskLevel


def test_machine_parse_probe_then_review_end_to_end():
    mock = MockLLM(responses={
        ModelRole.FLASH: [  # parse(结构化) + scrutinize初筛(结构化)
            {"claims": [{"bullet": "优化缓存QPS+50%", "tech": ["redis"],
                          "metric": "50", "source": "resume"}]},
            {"signals": [{"label": "no_embodied_detail", "quote": "就用单机redis",
                           "confidence": 0.7, }], "contradictions": []},
        ],
        ModelRole.PRO: [  # probe(结构化) + 深挖确认(结构化) + verdict结构化 + summary(generate)
            {"traps": [{"claim_idx": 0, "wrong_preset": "改成1800",
                         "question": "从200怎么调到1800？", "discriminators": ["纠正"]}]},
            {"confirmations": [{"index": 0, "confirmed": True, "note": "规模存疑"}]},
            {"overall": "MEDIUM", "by_dimension": {"no_embodied_detail": 0.8}},
            "技术规模存疑，建议人工复核。",
        ],
    })
    sm = AdversarialStateMachine(mock)
    claims, qs = sm.parse_then_probe("某简历全文")
    assert len(claims) == 1 and len(qs.questions) == 1
    report = sm.advance([__import__("adverhire.models", fromlist=["Claim"]).Claim("就用单机redis", source="answer")],
                         claims)
    assert report.overall == RiskLevel.MEDIUM
