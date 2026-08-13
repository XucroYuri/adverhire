---
name: adverhire
description: >
  对抗性招聘核验 —— 识别 AI 代答与简历注水，还原候选人真实能力。
  使用：当需要核验简历真实性、防 AI 提词器代答、生成对抗性面试提纲、
  做招聘测谎、hiredetector 排查简历水分时。
  触发词：adverhire、招聘测谎、简历核验、对抗性面试、AI 代答、简历注水。
---

# adverhire — 对抗性招聘测谎

给面试官/HR 用的辅助工具：围绕候选人简历自述内容，生成对抗性坑题、驱动动态追问，
识别 AI 代答与简历注水，输出风险分级报告。**工具只提供参考，不代面试官下结论。**

## 前置

- 引擎与驱动脚本在本仓库内。用绝对定位执行（仓库根下）：
  `.venv/bin/python scripts/verify.py`
- 完整方法论见 `references/adversarial-method.md`（五层问题体系 / 坑题三型 /
  判别三态 / 五维信号 / 三类矛盾 / 伦理红线）。

## 工作流

对你收到的候选人简历与回答，按下面流程走一遍：

### 1. 生成对抗性面试提纲

```bash
.venv/bin/python scripts/verify.py probe <resume文件> [-o 提纲.json]
```

（调试/验证可加 `--mock`，见下"验证"节。）输出结构：

```json
{ "claims": [...], "questions": [{ "question", "wrong_preset", "claim", "claim_idx", "discriminators" }] }
```

`questions` 即坑题列表，每条绑定一个真实简历断言（`claim`/`claim_idx`）。

### 2. 逐坑驱动动态追问（你实时执行，非脚本预编码）

这是全程最关键的对抗 loop。对**每个**坑题：

1. 用 `question` 向面试官/候选人提问。
2. 收到回答后，依你的判断分三态：

   - **纠正了坑的错误预设 / 说了具体数字/具身细节** → 命中，**即时终止此题**，标记"真才"。继续下一题。
   - **含糊 / 记不清 / 忘了** → 追问一层"具体到代码/数字/当时的取舍"。
   - **顺杆爬、复读泛化话** → 追问"那你改之前，线上实际发生了什么？"。

3. 每坑追问**最多 3 层**；一旦命中强signal（纠正/具身细节）就结束，不纠缠。
4. 把候选人的全部回答按顺序收集成一个 JSON 数组，存成临时文件（如 `/tmp/answers.json`）。

> 这就是"防 AI 代答"的核心：AI 提词器擅长标准追问，但答不出具身细节。你的
> 追问要落到简历里的具体数字、选型、当时取舍上，别停在通用八股。

### 3. 全程核验审查

```bash
.venv/bin/python scripts/verify.py review <resume文件> <answers.json> [-o 报告.json]
```

输出 `report`：

```json
{ "overall": "LOW|MEDIUM|HIGH",
  "signals": [{ "label", "quote", "confidence", "verdict_note" }],
  "contradictions": [{ "nature", "a", "b" }],
  "by_dimension": { "<五维>": <0~1> },
  "summary": "..." }
```

### 4. 向面试官解读（不要把结论说死）

- `overall` 是**风险分级**，不是淘汰/录用结论。HIGH 只代表"建议重点人工复核"，由面试官决断。
- `signals` 里每个都带 `quote` 证据链——指给面试官看"为什么这么判"。
- `by_dimension` **五维分开看**，别合并成一个总分掩盖信息。
- 综合你的追问观察（哪几题命中 corrected / 哪几题全程 echoed）一起给参考。

## 验证（Mock，无网络/密钥）

用现有 R1 白盒夹具做可复现的自检，验证"真 vs AI"判别性：

```bash
.venv/bin/python scripts/verify.py review tests/fixtures/real.md tests/fixtures/real_answers.json   --mock --responses tests/fixtures/responses/mock_review_real.json
.venv/bin/python scripts/verify.py review tests/fixtures/faked.md tests/fixtures/faked_answers.json --mock --responses tests/fixtures/responses/mock_review_faked.json
```

预期：`faked` 的信号数/`overall` 高于 `real`。这验证驱动层真正跑通全链路。

真实 LLM 冒烟（需自备凭证、按官方文档核对模型名）：
`API_KEY=... python scripts/verify.py review tests/fixtures/real.md tests/fixtures/real_answers.json`

## 伦理红线（硬约束）

1. 坑题永远派生自简历自述的断言，**不提出格/无关/无来源的刁难问题**。
2. **绝不输出"淘汰/录用"结论**——只给风险分级与参考，最终判断归人工。
3. 定位是辅助还原真实能力，不为了为难候选人。

## 边界（Phase-1 不做）

- 不做批量导入、Web 工作台、ATS/飞书集成（后续"壳"层）。
- 不依赖 MCP；自包含脚本 + 方法论即足够。
- 判别性的终极验证靠真实 LLM 冒烟，Mock 只保可复现的回归。
