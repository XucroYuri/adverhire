from adverhire.parse import parse_resume
from adverhire.llm import ModelRole, MockLLM
from adverhire.models import Claim

def test_parse_builds_claims_from_flash_response():
    mock = MockLLM(responses={ModelRole.FLASH: [{
        "claims": [
            {"bullet": "优化缓存 QPS+50%", "tech": ["redis"], "metric": "50", "source": "resume"},
            {"bullet": "自研压测工具", "tech": ["python"], "metric": None, "source": "resume"},
        ]
    }]})
    claims = parse_resume(mock, "某简历全文")
    assert [c.bullet for c in claims] == ["优化缓存 QPS+50%", "自研压测工具"]
    assert all(c.source == "resume" for c in claims)
    assert claims[0].metric == 50.0 and claims[1].metric is None
    assert mock.calls[0][0] == ModelRole.FLASH  # 解析用 Flash

def test_parse_handles_missing_technical_list():
    mock = MockLLM(responses={ModelRole.FLASH: [{"claims": [{"bullet": "纯文本", "tech": [], "metric": None, "source": "resume"}]}]})
    c = parse_resume(mock, "文本")[0]
    assert c.tech == [] and c.metric is None
