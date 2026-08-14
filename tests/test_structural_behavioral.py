"""结构化 + 行为特征判别测试（强鉴别能力框架，item 1/2）。

关键验证点：
- AI 包装（注入真人口吻词 + 假数字，能骗过旧的缺失式五维）会被新结构性/行为信号识别。
- 真才多轮深挖不误伤（平静短答收尾不算详情耗竭）。
- behavioral_uniformity（平滑恒定 vs 真人非均匀）+ idiosyncrasy_absence（跨段复用）。
"""
from adverhire.models import AnswerTurn, Claim
from adverhire.scrutinize import detect_structural, detect_behavioral, detect_overalignment
from adverhire.machine import AdversarialStateMachine


def _t(text, depth=0, latency=None, repaired=False, affect=False, reasoning=False):
    return AnswerTurn(text=text, depth=depth, answer_latency=latency,
                      self_repaired=repaired, affect_cue=affect, reasoning_visible=reasoning)


# —— detail_exhaustion：AI 深挖耗竭 vs 真才 terse 收尾 ——
def test_detail_exhaustion_fires_on_sustained_deep_vagueness():
    ai = [
        AnswerTurn("其实我用了redis优化，QPS到1800，效果不错。", depth=0),
        AnswerTurn("通过最佳实践和先进算法系统性提升了性能。", depth=1),
        AnswerTurn("全面优化了架构，达到行业领先水平。", depth=2),
    ]
    labels = {s.label for s in detect_structural(ai)}
    assert "detail_exhaustion" in labels


def test_no_detail_exhaustion_on_genuine_terse_closer():
    # 真才：具象 turn0/turn1 + 一句平静短答收尾 → 不算耗竭（非连续空洞）
    genuine = [
        AnswerTurn("其实当时卡在预热缓存命中率62%，用lua合了热点key回源才到94%，QPS从200到1200。", depth=0),
        AnswerTurn("不对，回滚那版是我改LRU搞的内存毛刺，回滚后加错峰预热任务收尾。", depth=1),
        AnswerTurn("总之折腾了两周才稳定。", depth=2),
    ]
    labels = {s.label for s in detect_structural(genuine)}
    assert "detail_exhaustion" not in labels


def test_idiosyncrasy_absence_fires_on_high_reuse():
    # 同构句式复用：单引擎批量生成残差
    verbose = [
        AnswerTurn("我们通过深度优化性能，显著提升系统效率，助力业务增长。", depth=0),
        AnswerTurn("我们通过深度重构架构，显著增强系统健壮，助力稳定运行。", depth=1),
        AnswerTurn("我们通过深度改进流程，显著提高交付质量，助力团队协作。", depth=2),
    ]
    labels = {s.label for s in detect_structural(verbose)}
    assert "idiosyncrasy_absence" in labels


# —— behavioral_uniformity：平滑恒定 vs 真人才认知轨迹 ——
def test_behavioral_uniformity_fires_on_smooth_instant_stream():
    machine = [
        _t("我们通过最佳实践优化，达到行业领先。", depth=0, latency=0),
        _t("我们通过先进算法增强，提升整体性能。", depth=1, latency=0),
        _t("我们通过体系化方法，实现跨越式提升。", depth=2, latency=0),
    ]
    labels = {s.label for s in detect_behavioral(machine)}
    assert "behavioral_uniformity" in labels


def test_no_uniformity_on_genuine_repair_affect_reasoning():
    human = [
        _t("其实当时卡在预热缓存命中率62%，回滚过一次。", depth=0, latency=3, repaired=True, affect=True, reasoning=True),
        _t("不对，改LRU那版是内存毛刺，回滚后加错峰任务。", depth=1, latency=2, repaired=True, affect=True, reasoning=True),
        _t("总之这套优化我踩了不少坑。", depth=2, latency=4, affect=True, reasoning=True),
    ]
    labels = {s.label for s in detect_behavioral(human)}
    assert "behavioral_uniformity" not in labels


# —— 端到端：AI 包装（注入真人口吻+假数字）仍被抓住，真才不误伤 ——
def test_endtoend_ai_polished_caught_genuine_not_hurt():
    sm = AdversarialStateMachine()
    claims = [Claim("优化缓存QPS", ["redis"], 50)]
    ai_polished = [
        _t("其实我用了redis，QPS提升到1800，效果很好。", depth=0, latency=0),
        _t("通过最佳实践和先进算法系统提升性能。", depth=1, latency=0),
        _t("提升整体性能，优化架构，达行业先进。", depth=2, latency=0),
    ]
    genuine = [
        _t("其实当时卡在预热缓存命中率62%，用lua合热点key回源才到94%，QPS从200到1200。", depth=0, latency=3, repaired=True, affect=True, reasoning=True),
        _t("不对，回滚那版是LRU内存毛刺，回滚后加错峰任务。", depth=1, latency=2, repaired=True, affect=True, reasoning=True),
        _t("总之这套优化我踩了不少坑，折腾两周才稳。", depth=2, latency=4, affect=True, reasoning=True),
    ]
    ra = sm.advance(ai_polished, claims, "疑似AI包装")
    rb = sm.advance(genuine, claims, "见真实细节")
    rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    assert rank[ra.overall.value] > rank[rb.overall.value]
    assert ra.overall.value == "HIGH"


# —— over_alignment：JD 过度对齐（求职侧 AI 模式 #1/#2/#7）——

_JD = ("高并发分布式后端，熟悉Redis缓存、Kafka消息队列、Docker部署、MySQL数据库、"
       "微服务架构，有性能优化经验，负责QPS压测与稳定性。")


def test_over_alignment_fires_on_jd_mirroring_resume():
    mirrored = [Claim("精通Redis缓存、Kafka消息队列、Docker、MySQL、微服务，QPS压测优化，高可用分布式，性能提升。",
                      source="resume")]
    labels = {s.label for s in detect_overalignment(mirrored, _JD)}
    assert "over_alignment" in labels


def test_over_alignment_not_on_genuine_resume():
    genuine = [Claim("主导过推荐系统缓存优化，用lua合热点key回源，命中率62%提到94%。", source="resume")]
    labels = {s.label for s in detect_overalignment(genuine, _JD)}
    assert "over_alignment" not in labels


def test_over_alignment_no_jd_returns_empty():
    assert detect_overalignment([Claim("x")], "") == []
