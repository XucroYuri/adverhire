# adverhire 对抗审查状态机 — 设计文档

> **日期**: 2026-08-13
> **状态**: 已获用户认可（brainstorming 产出）
> **核心原则**: 先做 Agent 能力，再做壳（界面层）

---

## 1. 问题定义与共识

AI 时代求职欺诈已形成全程链条：初筛环节求职者用 AI 包装与 HR 的首次接触（邮件/SMS/IM/ATS 聊天），在线面试环节用 AI 提词器实时代答。这种依赖本质上是求职者对自身能力增长的自我放任——用虚假信息掩盖真实水平。

`adverhire` 不把求职者当骗子，而是作为招聘方代表，用**对抗性审查与对抗性问答**，从虚假信息中筛选出"有思考、真实、有人类独特优势"的真人才。用 Agent 能力抵消 AI 带来的"超出自身实力的非合理优势"，让求职招聘市场回归真实。

### 已确认共识

| 决策点 | 结论 |
|--------|------|
| 对抗能力点 | A 坑题生成 + B 动态追问（问询线）+ C 虚构成分 + D 矛盾挖掘（审查线），四项全要 |
| 交付形态 | **薄壳 Agent 库**：Python 包 + CLI/测试脚本驱动，不碰 Web 工作台 UI |
| 模型分工 | V4 Pro 编推理环（坑题/追问/判定），V4 Flash 编量大不敏感环（解析/编排/扫描），多模型适配后置 |
| 验证数据 | 混合：先用白盒对照样本建已知答案基线，再换真实脱敏数据测复杂度 |
| 工程组织 | **单一对抗审查状态机**（方案 1），A/B/C/D 是同状态机的阶段而非独立 Agent |

---

## 2. 整体架构

### 2.1 状态机 `AdversarialStateMachine`

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────────┐
│  parse      │    │  probe       │    │  scrutinize  │    │  verdict    │
│  (V4 Flash) │───▶│  (V4 Pro)    │───▶│ (Flash粗筛   │───▶│  (V4 Pro)   │
│  简历解析    │    │  坑题生成    │    │  + Pro深挖)  │    │  评估报告    │
└─────────────┘    │  + 动态追问   │    │  虚构成分    │    └─────────────┘
                   └──────────────┘    │  矛盾挖掘    │
                                       └──────────────┘
```

### 2.2 阶段数据流

| 阶段 | 输入 | 输出 | 模型 | 心智 |
|------|------|------|------|------|
| `parse` | 原始简历文本/文件 | `Profile`（项目经历/技术栈/量化指标/时间线） | Flash | 量大、快、不敏感 |
| `probe` | `Profile` | `QuestionSet`（坑题 + 每坑追问候选） | Pro | 高区分度、Diff 敏感 |
| *(问答)* | `QuestionSet` + 候选人回答 | `AnswerLog[]` | — | 人介入 |
| `scrutinize` | `AnswerLog[]` | `FabricationSignals[]`(C) + `Contradictions[]`(D) | Flash 粗筛→Pro 深挖 | 先快后深 |
| `verdict` | 上述信号 | `RiskReport`（低/中/高 + 依据链） | Pro | 只提示，不下结论 |

### 2.3 数据模型

```python
@dataclass
class Claim:
    bullet: str            # 简历原文条目
    tech: list[str]
    metric: float | None
    source: str            # "resume" | "answer"

@dataclass
class ImpactedTrap:
    claim: Claim
    wrong_preset: str      # 故意植入的错误预设
    question: str
    discriminators: list[str]   # 判断真才 vs AI 的程序化判别指引

@dataclass
class FollowUp:
    ancestor_question: str  # 上一轮问题（同一坑题的父节点）
    branch: str             # 触发分支：vague / corrected / echoed
    question: str
    depth: int              # 当前深度（1 起）
    discriminator_hit: bool # 是否命中强判别信号（命中则此层为末层）

@dataclass
class QuestionSet:
    questions: list[ImpactedTrap]
    per_trap: dict[str, list[FollowUp]]

@dataclass
class Contradiction:
    claim_a: Claim
    claim_b: Claim
    nature: str            # tech_mismatch / scale_mismatch / timeline_conflict / procedural_contradiction

@dataclass
class SignalEvidence:
    label: str
    quote: str             # 命中的原文引用（可追溯）
    confidence: float
    verdict_note: str

@dataclass
class RiskReport:
    overall: RiskLevel            # LOW / MEDIUM / HIGH
    signals: list[SignalEvidence]
    contradictions: list[Contradiction]
    by_dimension: dict[Dimen, float]
    summary: str
```

### 2.4 反 AI 原则作为硬编码不变量（非提示词软约束）

1. **所有坑题永远派生自 `Claim`** —— 候选人自述的简历条目。probe 阶段无法提出格、无来源的问题。
2. **verdict 永不输出"淘汰/录用"** —— 只有低/中/高风险 + 依据链。放弃结论的生成权。

---

## 3. 问询线：坑题生成（A）+ 动态追问（B）

### 3.1 坑题生成（probe）

对每条可验证的 `Claim` 生成 `ImpactedTrap`，三类递增：

| 类型 | 机制 | 真才 / AI 的表现 |
|------|------|------|
| **A1 数值陷阱** | 把量化指标改成错误但合理的新值 | 真才纠正或描述真实曲线；AI 提词器照单全收 |
| **A2 技术细节陷阱** | 把技术选型/实现细节改成"看似合理但实际错" | 真才指出错误；AI 顺杆爬暴露没做过 |
| **A3 决策陷阱** | 植入"外行才会做"的决策，看是否反驳 | 真才解释权衡；AI 只会顺着肯定 |

**模型分工决策（用户已确认）**：
- A1/A3 可 Flash 粗生成 + Pro 复核。
- **A2 必须直接由 Pro 生成主坑**，不省这次 Pro 调用——因为 A2 需要模型真正理解技术正确用法后反推"看似合理但错误"的表述，是三者里区分度最高、最优化的 V4 Pro 推理舞台。成本优化时优先保 A2 的 Pro 配额。

### 3.2 动态追问（B）

每个坑题带追问状态机，形成树状追踪：

```
用户回答
  ├─ 含糊 → 追问1: "举具体代码/数字/当时取舍的例子"
  ├─ 纠正了我的错误(命中 discriminator) → 追问2: "当时你怎么发现的？"(半信半疑细节)
  └─ 顺杆爬(复读 AI) → 追问3: "你说改成了X，改之前线上发生了什么？"
        → 递归直到 B 终止条件
```

**终止条件（用户采纳"动态 3 层"）**：
1. 命中强判别信号（纠正陷阱 / 说出具身细节）→ **该层即末层**，已足够判定，不再消耗。
2. 已达深度上限（默认 3 层）。
3. 候选人明确表示不知道/记不清 → 记录"真实性低信号"，不纠缠。

B 由 V4 Pro 驱动，因为它要实时判断"该在哪个信号上深挖"，是决策环而非文本生成环。

---

## 4. 审查线：虚构成分检测（C）+ 矛盾挖掘（D）

### 4.1 两级管线（先快后深）

```
scrutinize(answers)
  → [Flash] 初筛: 扫描全部答案，产出全部候选 C 信号 + 候选 D 矛盾点
  → [Pro] 深挖: 只对初筛命中项，判定"真信号/误报"，附证据链
  → { fabrication_signals: [...], contradictions: [...] }
```

**误报/漏网策略**：Flash 初筛**宁可漏网不可误报**——漏网 Pro 还能兜底，但若先误报一堆垃圾，Pro 追问全浪费在否定它们上。裁量权交给 Pro。

### 4.2 C 虚构成分检测——客观可辨信号

对应立项 §3.3 五维评分，做成可机器检查的规则：

| 维度 | 信号 | 真才反例 |
|------|------|----------|
| 模板化套话 | 高密度"最佳实践"短语、无主语堆砌 | 具体到行为、第一人称 |
| 无具身细节 | 全抽象描述无代码/数字/取舍 | 具体到 incident / commit 触发点 |
| 逻辑泛化 | 一套方案套所有问题 | 承认边界、区分场景 |
| 情绪缺失 | 对"最难的坑"无数体感/懊悔/挣扎 | 有情绪词、真实反应 |
| 用词高度标准 | 无口语化、迟疑、修正痕迹 | 有"其实""当时我以为…" |

C 输出**带证据引用的信号 list**，每条指向回答原句，不搞"这段很 AI"式黑盒。

### 4.3 D 矛盾挖掘——跨源一致性

| 范围 | 找什么 |
|------|--------|
| 简历内（跨 Claim） | 技术栈/时间线/指标矛盾 |
| 简历 vs 回答 | 简历规模/技术 vs 回答对不上 |
| 回答轮次间（跨 AnswerLog） | 同一件事两次说法不同 |

`Contradiction{nature}` 标注冲突类型，便于聚合。

---

## 5. 评估报告（verdict）

- `overall` = LOW/MED/HIGH，**绝不出淘汰/录用结论**。
- 每条 `SignalEvidence` 带原文引用 `quote`，可追溯，不搞黑盒。
- **五维分开给且给成因**，不合并成总分掩盖信息——低分要说明是哪类信号导致。
- `by_dimension: dict[Dimen, float]` 的五维 `Dimen` 即 §4.2 C 的五个信号维度
  （`template_cliché / no_embodied_detail / over_generalization / missing_affect / over_standardized`），
  评分是各维度命中信号加权置信度（0–1），与 `overall` 分级的推导映射在实现期由 R1 白盒断言校准。

---

## 6. 薄壳交付（第一个可交付的"壳"）

**不碰 Web 工作台 UI。**

- **库 API**：`adverhire` Python 包，上述全部方法可被任何程序 `import` 调用。
- **CLI**：`adverhire inspect resume.pdf -o questions.json`，用于跑通链路、对照实验；输出 JSON/终端文本，不面向 HR 设计。
- 将来扩壳（CLI 工作台 / Web / API / ATS 集成）只需包住 `AdversarialStateMachine`，引擎零改动。

---

## 7. 测试策略（混合数据，先白盒后真实）

### 7.1 白盒基线（先建，已知答案）
- 同岗位虚构候选，造一对：
  - `real.md`：深度真实经历的手工简历 + 3 条真人自然回答。
  - `faked.md`：AI 生成的同岗位注水版简历 + 3 条 AI 提词器式回答。
- 断言：`probe` 对 `real.md` 生成更多 A2/A3 坑；`scrutinize` 判定 `faked.md` 的虚构成分/矛盾显著高于 `real.md`。

### 7.2 真实脱敏调优
- 换真实简历 + 真实面试回答，脱敏身份，跑同一套，调整 discriminators 与终止条件。

### 7.3 测试文件结构

```
tests/
  test_parse.py      # 简历→Profile 结构化正确
  test_probe.py      # 坑题派生自 Claim 且 A≥1 true positive
  test_followup.py   # 追问在纠正/含糊/顺杆爬信号下的分支正确
  test_scrutinize.py # C 标记真实 vs AI 回答，D 抓跨轮矛盾
  test_verdict.py    # 永不输出淘汰结论（不变量断言）
```

---

## 8. 待办 / 明确不做（YAGNI）

**本阶段明确不做**：
- Web 工作台 UI、批量简历导入、企业自定义配置、ATS/飞书/钉钉集成 → 壳层能力，能力验证后再说。
- LangGraph 多 Agent 编排、Milvus/RAG 检索、向量库 → MVP 不需要，属 §2 层级演进而非起始需求。
- 多模型适配层的完整实现 → 先固定 V4 Pro + V4 Flash 一条链路出结果。

**首个 demo 固定链路**：V4 Pro（probe/scrutinize 深挖/verdict）+ V4 Flash（parse/scrutinize 初筛）。具体 API 字符串名在写适配层时用官方文档核对。
