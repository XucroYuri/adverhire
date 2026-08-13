from __future__ import annotations

import re

from .models import Claim, Contradiction, SignalEvidence

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
    """比较两组断言(source 不同)：技术栈、规模、执行矛盾。

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
    return _dedupe(contradictions)


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
