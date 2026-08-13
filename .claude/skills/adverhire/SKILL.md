---
name: adverhire
description: >
  对抗性招聘核验 —— 识别 AI 代答与简历注水，还原候选人真实能力。
  Make sure to use this skill whenever the user asks to 核验简历真实性、防 AI 提词器代答、
  生成对抗性面试提纲、做招聘测谎、hiredetector 排查简历水分，或提到 AI 代答 / 简历注水 / 辨真才。
  触发词：adverhire、招聘测谎、简历核验、对抗性面试、AI 代答、简历注水、辨真才。
---

# adverhire — 对抗性招聘测谎

给面试官/HR 的辅助工具：围绕候选人简历自述内容，设计对抗性坑题、驱动动态追问，
识别 AI 代答与简历注水，输出风险分级报告。

**架构**：你是推理主体（会共情的面试官大脑）；确定性引擎是可测规则内核。负责判断的部分
（抽断言、设计坑题、判语义歧义、写总结）由你做；可复现的部分（归一化、校验不变量、
信号/矛盾/风险规则计算）由引擎做。**全程零外部 LLM API**。

> **前置**：所有 `python scripts/verify.py ...` 命令都在**仓库根目录**运行。若你在其它目录，
> 先 `cd` 回仓库根，否则引擎找不到。`-o` 产物务必用**唯一命名**（如 `/tmp/adverhire-<候选人>-*.json`），
> 避免同一会话跨候选人静默覆盖。

> **何时读方法论**：进入 §3/§4 做"三态判定 / 语义歧义落锤"前，先读
> `references/adversarial-method.md` 的 **坑题三型、判别三态表、五维信号表、矛盾三类**——
> 这些完整判据才是你落锤的依据，正文只是压缩摘要。

## 工作流

### 1. 从简历抽断言（你的推理）

读简历全文，逐条列出**可验证断言**：项目经历、技术栈、量化指标、决策。输出 JSON 数组
供引擎归一化。例如：

```json
[
  {"bullet": "优化缓存，QPS提升50%，命中率从62%提到94%", "tech": ["redis","lua"], "metric": 50},
  {"bullet": "主导推荐系统架构选型", "tech": ["kafka","docker"], "metric": null}
]
```

- 只要能验证的都抽：有数值、有具体技术、有决策取向的条目。
- 纯软技能（"沟通能力好"）别当可验证断言提。

> **零断言分支（先做这一步）**：运行 `tactics` 后，若返回 `{"tactics": []}` 或
> `{"claims": []}`（无可验证断言）——**立即停止**，告知面试官"该简历无可验证断言，
> 无法走技术对抗审查，建议改行为面试（behavioral）"。**不要**继续生成空坑题或产出一份
> 无信号的空报告。（空断言不代表求职者造假，只代表这段简历经不起技术核验。）

### 2. 拿坑题战术，设计具体坑题（你实时设计，非模板）

```bash
python scripts/verify.py tactics --claims /tmp/adverhire-<候选人>-claims.json -o /tmp/adverhire-<候选人>-tactics.json
```

引擎返回每个断言的坑题**战术**（A1 数值 / A2 技术细节 / A3 决策 + 切入角度）。
**你负责把战术变成"只有真做过才察觉"的具体坑题**：

```bash
python scripts/verify.py validate --claims /tmp/adverhire-<候选人>-claims.json --traps /tmp/adverhire-<候选人>-traps.json -o /tmp/adverhire-<候选人>-questions.json
```

`traps.json` 每项：`{claim_idx, question, wrong_preset, discriminators}`。`discriminators`
**可为空**——空时该坑的 corrected 分支永不触发，只能靠多追问（最多 3 层）观察，并把
"空 discriminators"当作"该坑区分度较弱"的记录。

**坑题设计质量自检**（A2 优先，区分度最高）：
- A1 数值：量化指标改成**错误但合理**的新值，请确认/纠正。
- A2 技术细节：实现细节/选型改成**看似合理但实际错**的表述——最杀 AI 提词器。
- A3 决策：植入**外行才会选**的决策，看是否解释权衡。
- 坑题永远派生自简历断言，不提出格问题（引擎强制校验，违反会报错）。
- **拿不准就降级**：如果你不确定某技术栈的真实细节，别硬造"看似合理实则错"的 A2——
  一个被候选人一眼看穿的假坑题，先暴露的是你的不专业。拿不准就退到 A1/A3，更稳。
- `discriminators`：列命中即判"真才"的词（如"其实""回滚""踩"）。

### 3. 逐坑动态追问（你的实时判断）

对每个坑题，用 `question` 提问，收到回答后判三态：
- **corrected**：纠正了坑错预设 / 给具体数字、具身细节 → **即刻终止此题**，记录真才信号。
- **vague**：含糊/记不清 → 追问一层"具体到代码、数字、当时的取舍"。
- **echoed**：顺杆爬、复读泛化 → 追问"那你改之前，线上实际发生了什么？"。

追问措辞由你实时写。每坑最多 3 层；命中 corrected 即停。把候选人**全部回答**按顺序存
JSON 数组供 review。

> **异常样本判别**：真才通常有 1-2 条平静短答。若 detect_signals 几乎把每句都判
> `no_embodied_detail`，或你几乎全程判 echoed——可能是样本太少或提示漂移。缩小范围
> 就最硬的那个断言重新追问，别据此直接下"造假"结论。

### 4. 全程核验

```bash
python scripts/verify.py review --claims /tmp/adverhire-<候选人>-claims.json --answers /tmp/adverhire-<候选人>-answers.json \
  --summary "你依据证据链写的一句话参考给面试官" -o /tmp/adverhire-<候选人>-report.json
```

引擎用纯规则跑 `detect_signals`（五维）+ `detect_contradictions` + `grade_risk`。
**你对语义歧义点落锤**：detect_signals 是启发式——"真人口吻但无数字"可能误报
`no_embodied_detail`，你要结合上下文判是真 AI 味还是真人才的简练，据此修正 `--summary`。

> **引擎报错路径**：若任一子命令非零退出 / 抛 traceback——读 stderr，修正输入
> （通常是 `traps.json` 字段缺漏、`claims` 不是 list、路径错误），重试一次；仍失败就停下，
> 把原始 stderr 报告给面试官，**不要静默编一份报告**。

### 5. 向面试官解读（别把结论说死）

- `overall` 是**风险分级**（LOW/MED/HIGH），不是淘汰/录用结论。HIGH 只代表"建议重点人工复核"。
- `signals` 每条带 `quote` 证据链，指给面试官看"为什么这么判"。
- `by_dimension` 五维分开看，别合并成总分。
- 综合你的追问观察（哪几题命中 corrected / 全程 echoed）+ 引擎信号一起给参考。

## 判别性验证（纯规则，无 LLM，可复现）

用 R1 白盒基线跑一遍，确认真 vs AI 有区分。命令如下（**仓库根执行**）：

```bash
# 1) 从 real.md 抽出的可验证断言写进 claims.json（按 §1 格式）
# 2) 真实回答应低风险
python scripts/verify.py review --claims /tmp/adverhire-real-claims.json \
  --answers tests/fixtures/real_answers.json -o /tmp/adverhire-real-report.json

# 3) AI 注水应高风险（faked_answers.json 即代表 AI 提词器式回答）
python scripts/verify.py review --claims /tmp/adverhire-faked-claims.json \
  --answers tests/fixtures/faked_answers.json -o /tmp/adverhire-faked-report.json
```

预期：`real` → `overall` 偏低、signals 少或零星；`faked` → `overall` 偏高、signals 多条
（无具身/泛化/模板化）。若两者不区分，说明规则需调优，**别把结果伪作"已验证"**。

## 伦理红线（硬约束）

1. 坑题永远派生自简历自述断言，**不提出格/无关/无来源的刁难问题**。
2. **绝不输出"淘汰/录用"结论**——只给风险分级 + 证据链，决策归人工。
3. 定位是辅助还原真实能力，维护招聘公平，不为了为难候选人。

## 边界（Phase 1 不做）

- 不建 MCP、不接外部 LLM API、不做批量/Web 工作台/ATS 集成。
- 判别性的上限取决于你的共情推理（坑题是否够隐蔽、语义歧义判得准）——这是核心竞争力，
  也是"双主体架构"里你承担的那一半。
