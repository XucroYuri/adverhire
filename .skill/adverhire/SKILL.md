---
name: adverhire
description: >
  对抗性招聘核验 —— 识别 AI 代答与简历注水，还原候选人真实能力。
  使用：当需要核验简历真实性、防 AI 提词器代答、生成对抗性面试提纲、
  做招聘测谎、hiredetector 排查简历水分时。
  触发词：adverhire、招聘测谎、简历核验、对抗性面试、AI 代答、简历注水。
---

# adverhire — 对抗性招聘测谎

给面试官/HR 的辅助工具：围绕候选人简历自述内容，设计对抗性坑题、驱动动态追问，
识别 AI 代答与简历注水，输出风险分级报告。

**架构**：你是推理主体（会共情的面试官大脑）；确定性引擎是可测规则内核。你负责
需要判断的部分（从简历抽断言、设计坑题、落锤语义歧义、写总结）；引擎负责可复现的
部分（数据结构、归一化、校验不变量、信号/矛盾/风险的规则计算）。**全程零外部 LLM API**。

## 工作流

### 1. 从简历抽断言（你用自己的推理做）

读简历全文，逐条列出**可验证断言**：项目经历、技术栈、量化指标、决策。输出成一个
JSON 数组，供引擎归一化。例如：

```json
[
  {"bullet": "优化缓存，QPS提升50%，命中率从62%提到94%", "tech": ["redis","lua"], "metric": 50},
  {"bullet": "主导推荐系统架构选型", "tech": ["kafka","docker"], "metric": null}
]
```

- 只要能验证的都要抽：有数值、有具体技术、有决策取向的条目。
- 纯软技能（"沟通能力好"）别当可验证断言提——引擎会过滤掉不可验证项。

### 2. 拿坑题战术，设计具体坑题（核心：你实时设计，非模板）

```bash
python scripts/verify.py tactics --claims /tmp/claims.json -o /tmp/tactics.json
```

引擎返回每个断言的坑题**战术**（A1 数值 / A2 技术细节 / A3 决策 + 切入角度）。
**你负责把战术变成"只有真做过才察觉"的具体坑题**：

```bash
python scripts/verify.py validate --claims /tmp/claims.json --traps /tmp/traps.json -o /tmp/questions.json
```

`traps.json` 每项：`{claim_idx, question, wrong_preset, discriminators}`。

**坑题设计质量自检**（A2 优先，区分度最高）：
- A1 数值：把断言里的量化指标改成**错误但合理**的新值，请候选人确认/纠正。
- A2 技术细节：把实现细节/选型改成**看似合理但实际错**的表述——这是最杀 AI 提词器的一型。
- A3 决策：植入**外行才会选**的决策，看是否解释权衡。
- 坑题永远派生自简历断言，不提出格/无关问题（引擎会强制校验这条下限）。
- `discriminators`：列当回答命中哪些词/信号时应判为"真才"（如"其实""回滚""踩"）。

### 3. 逐坑动态追问（你的实时判断）

对每个坑题，用 `question` 提问，收到回答后判三态（引擎可辅助）：
- **corrected**：纠正了坑错预设 / 说具体数字/具身细节 → **即刻终止此题**，记录真才信号。
- **vague**：含糊/记不清 → 追问一层"具体到代码、数字、当时的取舍"。
- **echoed**：顺杆爬、复读泛化 → 追问"那你改之前，线上实际发生了什么？"。

追问措辞由你实时写。每坑最多 3 层；命中 corrected 即停。把候选人的**全部回答**按
顺序存 JSON 数组。

### 4. 全程核验

```bash
python scripts/verify.py review --claims /tmp/claims.json --answers /tmp/answers.json \
  --summary "你依据证据链写的一句话参考给面试官" -o /tmp/report.json
```

引擎用纯规则跑 `detect_signals`（五维）+ `detect_contradictions` + `grade_risk`。
**你对语义歧义点落锤**：detect_signals 是启发式——个别"真人口吻但无数字"的回答可能误报
`no_embodied_detail`，你要结合上下文判断是真 AI 味还是真人才该有的简练，据此修正 `--summary`
或提醒面试官。

### 5. 向面试官解读（不要把结论说死）

- `overall` 是**风险分级**（LOW/MED/HIGH），不是淘汰/录用结论。HIGH 只代表"建议重点人工复核"。
- `signals` 每条带 `quote` 证据链——指给面试官看"为什么这么判"。
- `by_dimension` 五维分开看，别合并成总分掩盖信息。
- 综合你的追问观察（哪几题命中 corrected / 哪几题全程 echoed）+ 引擎信号一起给参考。

## 判别性验证（纯规则，无 LLM）

用 R1 白盒基线走一遍真实流程，确认真 vs AI 有区分：对 `tests/fixtures/real.md`（真实经历）
抽断言→tactics→review，与 `tests/fixtures/faked.md`（AI 注水）对照。预期：
- real 的回答 → `overall` 偏低、signals 少或零星。
- faked 的回答 → `overall` 偏高、signals 多条（无具身/泛化/模板化）。

## 伦理红线（硬约束）

1. 坑题永远派生自简历自述断言，**不提出格/无关/无来源的刁难问题**。
2. **绝不输出"淘汰/录用"结论**——只给风险分级 + 证据链，最终判断归人工。
3. 定位是辅助还原真实能力，维护招聘公平，不为了为难候选人。

## 边界（Phase 1 不做）

- 不建 MCP、不接外部 LLM API、不做批量/Web 工作台/ATS 集成。
- 判别性的上限取决于你的共情推理（坑题是否够隐蔽、语义歧义是否判得准）——
  这是本工具的核心竞争力，也是 README 所述"双主体架构"里你承担的那一半。
