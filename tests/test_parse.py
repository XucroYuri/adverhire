from adverhire.parse import normalize_claims


def test_normalize_claims_builds_claim_objects():
    claims = normalize_claims([
        {"bullet": "优化缓存 QPS+50%", "tech": ["redis", "lua"], "metric": "50", "source": "resume"},
        {"bullet": "自研压测工具", "tech": ["python"], "metric": None, "source": "resume"},
    ])
    assert [c.bullet for c in claims] == ["优化缓存 QPS+50%", "自研压测工具"]
    assert claims[0].metric == 50.0 and claims[0].tech == ["redis", "lua"]
    assert all(c.source == "resume" for c in claims)


def test_normalize_claims_defaults_metric_and_source():
    claims = normalize_claims([{"bullet": "纯文本", "tech": [], "metric": None}])
    assert claims[0].metric is None
    assert claims[0].source == "resume"


def test_to_float_rejects_inf_and_nan():
    claims = normalize_claims([
        {"bullet": "inf", "tech": ["x"], "metric": "inf", "source": "resume"},
        {"bullet": "nan", "tech": ["x"], "metric": "nan", "source": "resume"},
    ])
    assert claims[0].metric is None
    assert claims[1].metric is None


def test_normalize_claims_handles_empty_and_garbage():
    assert normalize_claims([]) == []
    claims = normalize_claims([{"bullet": "abc", "tech": [], "metric": "not-a-number"}])
    assert claims[0].metric is None
