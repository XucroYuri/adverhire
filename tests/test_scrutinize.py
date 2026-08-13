from adverhire.scrutinize import scrutinize
from adverhire.llm import ModelRole, MockLLM
from adverhire.models import Claim

RESUME = [Claim("优化缓存 QPS+50%", ["redis"], 50.0, "resume")]
ANSWER = Claim("我们用了单机 redis 就够了", ["redis"], None, "answer")

def test_scrutinize_confirmed_signal_survives():
    mock = MockLLM(responses={
        ModelRole.FLASH: [{
            "signals": [
                {"label": "no_embodied_detail", "quote": "用单机redis就够了", "confidence": 0.7},
            ],
            "contradictions": [],
        }],
        ModelRole.PRO: [{"confirmations": [{"index": 0, "confirmed": True, "note": "无具身细节,规模存疑"}]}],
    })
    sigs, contras = scrutinize(mock, [ANSWER], RESUME)
    assert len(sigs) == 1 and sigs[0].label == "no_embodied_detail"
    assert contras == []

def test_scrutinize_rejects_false_positive():
    mock = MockLLM(responses={
        ModelRole.FLASH: [{
            "signals": [{"label": "template_cliche", "quote": "xxx", "confidence": 0.8}],
            "contradictions": [],
        }],
        ModelRole.PRO: [{"confirmations": [{"index": 0, "confirmed": False, "note": "误报"}]}],
    })
    sigs, _ = scrutinize(mock, [ANSWER], RESUME)
    assert sigs == []  # 误报被 Pro 驳回
