from adverhire.scrutinize import detect_signals, detect_contradictions
from adverhire.models import Claim


def _claim(text: str, tech=None, metric=None, source="answer"):
    return Claim(text, tech or [], metric, source)


def test_detect_signals_flags_vague_ai_answer():
    answers = [_claim("通过深度优化缓存架构和引入先进算法，系统性提升了整体性能，达到业界领先水平。")]
    signals = detect_signals(answers)
    labels = {s.label for s in signals}
    # AI 式的空泛高水分回答应命中多个维度
    assert "no_embodied_detail" in labels        # 无数字/代码
    assert "over_generalization" in labels       # 通过X提升Y且无主语
    assert "missing_affect" in labels            # 无情绪锚点


def test_detect_signals_clean_for_embodied_answer():
    answers = [_claim("其实当时坑在预热缓存命中率62%，我们用lua脚本合了热点key批量回源，才提到94%，我回滚过那版。")]
    signals = detect_signals(answers)
    labels = {s.label for s in signals}
    assert "no_embodied_detail" not in labels    # 有数字/代码
    assert "over_generalization" not in labels   # 有第一人称
    assert "missing_affect" not in labels        # 有"其实/当时/回滚"


def test_detect_contradictions_tech_mismatch():
    a = _claim("主导 Redis 缓存优化", tech=["redis"], source="resume")
    b = _claim("我们主要用 MongoDB 做主存", tech=["mongodb"], source="answer")
    contras = detect_contradictions([a], [b])
    assert any(c.nature == "tech_mismatch" for c in contras)
    assert any(c.a is a and c.b is b for c in contras)


def test_detect_contradictions_scale_mismatch():
    a = _claim("QPS 提升50%", tech=[], metric=50.0, source="resume")
    b = _claim("QPS 到 1800", tech=[], metric=1800.0, source="answer")
    contras = detect_contradictions([a], [b])
    assert any(c.nature == "scale_mismatch" for c in contras)


def test_detect_contradictions_no_false_positive_on_same_tech():
    a = _claim("优化缓存", tech=["redis"], source="resume")
    b = _claim("我们用redis做了热点处理", tech=["redis"], source="answer")
    assert detect_contradictions([a], [b]) == []
