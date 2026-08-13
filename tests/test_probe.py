from adverhire.probe import gen_traps
from adverhire.llm import ModelRole, MockLLM
from adverhire.models import Claim

CLAIMS = [
    Claim("优化缓存 QPS+50%", ["redis"], 50.0, "resume"),
    Claim("纯文本条目", [], None, "resume"),          # 不可验证，不应生成坑题
]

def test_gen_traps_uses_pro_and_keeps_manifested_traps():
    mock = MockLLM(responses={ModelRole.PRO: [{
        "traps": [
            {"claim_idx": 0, "wrong_preset": "从200调到1800",
             "question": "从200怎么一步步调到1800的？",
             "discriminators": ["纠正数值", "描述增长曲线"]},
        ]
    }]})
    qs = gen_traps(mock, CLAIMS)
    assert len(qs.questions) == 1
    assert qs.questions[0].claim is CLAIMS[0]
    assert mock.calls[0][0] == ModelRole.PRO  # 坑题用 Pro

def test_gen_traps_discards_out_of_range_claim_idx():
    mock = MockLLM(responses={ModelRole.PRO: [{
        "traps": [
            {"claim_idx": 0, "wrong_preset": "p", "question": "q0", "discriminators": []},
            {"claim_idx": 99, "wrong_preset": "p", "question": "q-bad", "discriminators": []},
        ]
    }]})
    qs = gen_traps(mock, CLAIMS)
    assert len(qs.questions) == 1 and qs.questions[0].question == "q0"
