from adverhire.llm import ModelRole, MockLLM

def test_model_role_values():
    assert {r.value for r in ModelRole} == {"pro", "flash"}

def test_mock_llm_returns_queued_and_records_calls():
    mock = MockLLM(responses={ModelRole.PRO: ["a", "b"]})
    assert mock.generate(ModelRole.PRO, "q1") == "a"
    assert mock.generate(ModelRole.PRO, "q2") == "b"
    assert [(r, p) for r, p, _ in mock.calls] == [(ModelRole.PRO, "q1"), (ModelRole.PRO, "q2")]

def test_mock_llm_structured_returns_dict():
    mock = MockLLM(responses={ModelRole.FLASH: [{"claims": 2}]})
    out = mock.structured(ModelRole.FLASH, "p", {"type": "object"})
    assert out == {"claims": 2}
