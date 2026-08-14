from __future__ import annotations

import re

from .models import Claim, Contradiction, SignalEvidence, AnswerTurn

# —— 五维虚构成分信号（纯规则启发式，subagent 对语义歧义点可落锤）——

# 模板化套话高频词：无具体主语/行为的高密度包装词
_TEMPLATE_BUZZ = (
    "最佳实践", "业界领先", "显著提升", "大幅", "赋能", "助力",
    "全面", "先进", "卓越", "标杆", "体系化", "创新",
)
# 具身细节锚点：只有"具体实现"才算数——命名库/具体运维动作/具体指标词/代码动作。
# 泛化概念词（缓存/架构/算法/接口/数据库/性能）不算——那恰恰是 AI 注水常用词。
_HAS_NUM = re.compile(r"\d+")
_HAS_TECH_WORD = re.compile(
    r"(select|insert|update|join|deploy|commit|git|rollback|回滚|"
    r"lua|redis|kafka|docker|nginx|mysql|mongodb|k8s|kubernetes|serverless|"
    r"压测|线上|灰度|qps|tps|p99|命中率|吞吐|延迟|毫秒|并发|脚本)"
)
# 情绪/体感锚点
_AFFECT_ANCHORS = ("其实", "当时", "折腾", "踩坑", "后悔", "回滚",
                   "总算", "没想到", "后来", "才", "不太", "翻车", "踩了一遍")
# 口语化/自我修正痕迹（真人口吻）
_SPOKEN_ANCHORS = ("其实", "好像", "应该是", "我记不清", "大概", "反正",
                   "说白了", "当时我觉得", "我踩", "翻过", "回滚过", "忘了")


def _detect_dimension(text: str) -> list[SignalEvidence]:
    """对单个回答文本，跑五维启发式，返回命中的信号(带原句证据)。"""
    signals: list[SignalEvidence] = []

    # 1. 模板化套话：命中多个空泛包装词且无具身（主语缺失）
    hits = [w for w in _TEMPLATE_BUZZ if w in text]
    if len(hits) >= 2:
        signals.append(SignalEvidence(
            label="template_cliche", quote=text[:120],
            confidence=min(1.0, 0.5 + 0.1 * len(hits)),
            verdict_note=f"命中模板化套话词：{'、'.join(hits)}",
        ))

    # 2. 无具身细节：无数字、无具体技术/代码表征
    if not _HAS_NUM.search(text) and not _HAS_TECH_WORD.search(text):
        signals.append(SignalEvidence(
            label="no_embodied_detail", quote=text[:120],
            confidence=0.8,
            verdict_note="回答无数字/代码/具体技术锚点，全是抽象描述",
        ))

    # 3. 逻辑泛化：陈述是"通过…提升了…"式，无第一人称具体行为
    if ("通过" in text or "采用" in text) and "我" not in text and "我们" not in text:
        signals.append(SignalEvidence(
            label="over_generalization", quote=text[:120],
            confidence=0.7,
            verdict_note="泛化的'通过X提升Y'句式，缺少第一人称的具体做法",
        ))

    # 4. 情绪缺失：对涉身经历无任何情绪/体感锚点
    if not any(a in text for a in _AFFECT_ANCHORS):
        signals.append(SignalEvidence(
            label="missing_affect", quote=text[:120],
            confidence=0.6,
            verdict_note="无情绪/体感锚点，回答缺乏亲身经历的真实痕迹",
        ))

    # 5. 用词高度标准：无任何口语化/自我修正痕迹
    if not any(s in text for s in _SPOKEN_ANCHORS):
        signals.append(SignalEvidence(
            label="over_standardized", quote=text[:120],
            confidence=0.6,
            verdict_note="用词高度规整，无'其实/好像/记不清'等真人口吻",
        ))

    return signals


def detect_signals(answers: list[Claim]) -> list[SignalEvidence]:
    """对全部回答跑五维虚构成分启发式。语义歧义点由 subagent 落锤。"""
    signals: list[SignalEvidence] = []
    for answer in answers:
        signals.extend(_detect_dimension(answer.bullet))
    return signals


# —— 跨源矛盾（纯规则一致性检查）——

def _techs(claim: Claim) -> set[str]:
    return {t.lower() for t in claim.tech}


def detect_contradictions(claims_a: list[Claim], claims_b: list[Claim]) -> list[Contradiction]:
    """比较两组断言(source 不同)：技术栈、规模、时间线/执行矛盾。

    纯规则命中确定性矛盾；语义层矛盾由 subagent 判断。
    """
    contradictions: list[Contradiction] = []
    for a in claims_a:
        for b in claims_b:
            # 技术栈矛盾：A 自称主导某技术，B 宣称完全不同且无交集
            ta, tb = _techs(a), _techs(b)
            if ta and tb and not (ta & tb):
                contradictions.append(Contradiction(
                    a=a, b=b,
                    nature="tech_mismatch",
                ))
            # 规模矛盾：A、B 都带量化指标但量级悬殊(>10x)
            if a.metric is not None and b.metric is not None and a.metric > 0 and b.metric > 0:
                ratio = max(a.metric, b.metric) / min(a.metric, b.metric)
                if ratio > 10:
                    contradictions.append(Contradiction(
                        a=a, b=b, nature="scale_mismatch",
                    ))
            # 时间线/前后矛盾：字面级只做"改款的同一断言两来源说法互斥"的兜底；
            # 语义时间线由 subagent 落锤。确定性的 procedural 矛盾：A、B bullet 高度重合但措辞打架。
            if a.bullet and b.bullet and _bigrams(a.bullet) & _bigrams(b.bullet) \
                    and ("改了" in a.bullet or "之前" in a.bullet) \
                    and ("现在" in b.bullet or "目前" in b.bullet or "单点" in b.bullet):
                contradictions.append(Contradiction(a=a, b=b, nature="procedural_contradiction"))
    return _dedupe(contradictions)


# —— 结构性 + 行为特征信号（item 1/2，难被 AI 模仿）——

def _concreteness(text: str) -> float:
    """具体锚点密度：数字 + 命名的具体技术/实例，按长度归一。AI 可注入假数字，故单看不足凭。"""
    nums = len(re.findall(r"\d+(?:\.\d+)?%?", text))
    tech_hits = len([w for w in _HAS_NUM_TECH_WORDS if w in text])
    length = max(1, len(text))
    return (nums + 0.5 * tech_hits) / length


# 命名具体实例技术词（比 _HAS_TECH_WORD 更"命名/实例"向：真经历里的点名）
_HAS_NUM_TECH_WORDS = (
    "redis", "kafka", "docker", "nginx", "mysql", "mongodb", "lua", "k8s",
    "qps", "tps", "p99", "毫秒", "延迟", "命中率", "压测", "回滚", "灰度", "线上",
)


def detect_structural(turns: list[AnswerTurn]) -> list[SignalEvidence]:
    """结构性信号：详情耗竭（随深度具体密度下降）+ 跨段复用（单引擎批量生成的残差）。

    核心原理：真经历深挖时具体密度递增；假经历浅层答好、深层跌回泛化。
    """
    signals: list[SignalEvidence] = []
    if len(turns) < 2:
        return signals

    # 2.1 详情耗竭：深挖后具体密度下降而无法重新接续。
    #    真才常以一句平静短答总结收尾（具象 1-2 条 + 一条 summary），单条收尾不算耗竭。
    #    只有"被追问到深处后连续 ≥2 轮都答不出具象"（无法重新接续）才算耗竭。
    deep_vague_streak = 0
    max_streak = 0
    for t in sorted(turns, key=lambda x: x.depth):
        if t.depth >= 1 and _concreteness(t.text) < 0.003:
            deep_vague_streak += 1
            max_streak = max(max_streak, deep_vague_streak)
        else:
            deep_vague_streak = 0
    if max_streak >= 2:
        signals.append(SignalEvidence(
            label="detail_exhaustion", quote=turns[-1].text[:120],
            confidence=0.7,
            verdict_note="被追问到深处后连续多轮答不出具象细节，无法重新接续（详情耗竭）",
        ))
    # 从浅到深全程无命名实例/数字锚点（一条具象都没有）也记一条，置信度低
    if all(_concreteness(t.text) < 0.002 for t in turns):
        signals.append(SignalEvidence(
            label="detail_exhaustion", quote=turns[-1].text[:120],
            confidence=0.5, verdict_note="从浅到深全程无命名实例/数字锚点",
        ))

    # 2.3 独特性残差缺失：跨段高度复用=单引擎批量生成。
    #    用字符 bigram Jaccard 逼近"同构句式复用"。真才同话题会在内容词上复用，
    #    但 Skeleton 级高复用(≥3 轮 + >0.15)指向"单个生成器批量套模板"而非独立经历。
    if len(turns) >= 3:
        reuse = _cross_reuse([t.text for t in turns])
        if reuse > 0.15:
            signals.append(SignalEvidence(
                label="idiosyncrasy_absence", quote=turns[0].text[:120],
                confidence=min(1.0, reuse * 2),
                verdict_note=f"多段回答高度同构复用（相似度{reuse:.2f}），像单个引擎批量生成而非独立经历",
            ))
    return signals


def _bigrams(s: str):
    return {s[i:i + 2] for i in range(len(s) - 1)} if len(s) > 1 else set()


def _cross_reuse(texts: list[str]) -> float:
    if len(texts) < 2:
        return 0.0
    total, n = 0.0, 0
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            a, b = _bigrams(texts[i]), _bigrams(texts[j])
            if not (a and b):
                continue
            total += len(a & b) / len(a | b)
            n += 1
    return total / n if n else 0.0


def detect_behavioral(turns: list[AnswerTurn]) -> list[SignalEvidence]:
    """行为流信号：整场行为是否'平滑恒定'(机器) vs 非均匀(真人)。

    真人深挖下出现自我修正/情绪起伏/露出推理/思考延迟；AI 提词器平滑恒定、秒答、无挣扎。
    只有 subagent 观察到的字段被使用；未观察(默认值)时不算匹配。
    """
    signals: list[SignalEvidence] = []
    if len(turns) < 2:
        return signals

    repaired = sum(1 for t in turns if t.self_repaired)
    affect = sum(1 for t in turns if t.affect_cue)
    reasoning = sum(1 for t in turns if t.reasoning_visible)
    # 秒答占比（latency 被观察到且≈0）
    observed_lat = [t for t in turns if t.answer_latency is not None]
    instant_ratio = (sum(1 for t in observed_lat if t.answer_latency == 0) / len(observed_lat)) if observed_lat else None

    human_markers = repaired + affect + reasoning
    if human_markers == 0:
        confidence = 0.7 if len(observed_lat) == len(turns) and instant_ratio == 1.0 else 0.5
        signals.append(SignalEvidence(
            label="behavioral_uniformity", quote=turns[0].text[:120],
            confidence=confidence,
            verdict_note=(f"整场无自我修正/情绪起伏/推理外露"
                          + (f"，且全程秒答(占比{instant_ratio:.0%})" if instant_ratio is not None else "")),
        ))
    return signals


def _dedupe(contradictions: list[Contradiction]) -> list[Contradiction]:
    seen: set[tuple] = set()
    out: list[Contradiction] = []
    for c in contradictions:
        key = (c.nature, c.a.bullet, c.b.bullet)
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out
