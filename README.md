# adverhire · 招聘测谎仪

> **adverhire** = Adversarial Hiring Agent（对抗性招聘智能体）
> **传播心智**：**hiredetector（招聘测谎仪）** —— 给面试装个测谎仪，让招聘回归真实能力。

`adverhire` 是一个对抗性招聘核验工具：围绕候选人简历，生成定制化对抗性坑题，驱动动态追问，
系统性识别 **AI 代答、简历注水与经历造假**，为面试官提供客观的真实性参考。

它不是刁难候选人的工具，而是建立一套**公平的核验机制**——让简历回归真实、让面试回归能力，
帮招聘方找到真正匹配的人才，也让踏实做事的求职者不被劣币驱逐。

## 它解决什么

AI 时代求职欺诈已成全程链条：初筛用 AI 包装与 HR 的首次接触，在线面试用 AI 提词器实时代答。
传统面试题库、标准化提问已全面失效，面试官面对"完美回答"越来越难区分真实能力与 AI 生成内容。

- **简历注水难辨**：AI 生成的项目经历光鲜完整，HR 初筛几乎无法甄别。
- **面试作弊隐蔽**：AI 实时代答可输出标准化工整答案，常规提问难以识别。
- **核验效率低**：面试官靠个人经验设计细节追问，没有标准化方法论。

`adverhire` 用 Agent 抵消"超出自身实力"的非合理优势，帮面试官穿透套话、还原真实。

## 工作原理

引擎是一个可测的对抗审查状态机：`parse → probe → scrutinize → verdict`

```text
简历 ──parse──▶ 结构化断言 Claims
                 └─probe──▶ 对抗性坑题（针对具体数值/技术选型/决策植入错误前提）
                              ├─(追问 loop) 逐坑问答，动态判三态，最多追问 3 层
                              └────────────▶ scrutinize──▶ 虚构成分信号 + 矛盾挖掘
                                                          └─verdict──▶ 风险分级报告（LOW/MED/HIGH）
```

**两条铁律（硬编码不变量）**：
- 所有坑题**永远派生自候选人自述的简历断言**——不提出格、无来源的刁难问题。
- `verdict` **永不输出"淘汰/录用"结论**——只给风险分级 + 证据链，最终判断归人工。

## 形态：Agent Skill + CLI

`adverhire` 以 **Skill + CLI** 形态运行在 Claude Code / Codex 等 Agent 框架下——
Agent 框架本身就是交互壳，无需自建 Web 工作台。能力内核是可测的 Python 库，交互皮肤是 agent 原生循环。

### 作为 Claude Code Skill（推荐）

在 Claude Code 中执行 `/adverhire`，将自动加载：
- **生成面试提纲**：围绕简历产出对抗性坑题 + 每坑的追问提示
- **驱动动态追问**：逐坑问答，判定 corrected/vague/echoed，自动分支深挖
- **全程核验**：扫描虚构成分信号 + 跨来源矛盾
- **输出风险报告**：五维评分 + 证据链，绝不代下结论

方法论文档见 `.skill/adverhire/references/adversarial-method.md`
（五层问题体系 / 坑题三型 / 判别三态 / 五维信号 / 三类矛盾 / 伦理红线）。

### 直接命令行

```bash
# 生成对抗性面试提纲（坑题列表，绑定每个简历断言）
python scripts/verify.py probe <resume.md> -o 提纲.json

# 进候答 + 全程核验（answers 为候选回答 JSON 数组）
python scripts/verify.py review <resume.md> <answers.json> -o 报告.json
```

`review` 输出结构：

```json
{ "overall": "HIGH",            // LOW / MEDIUM / HIGH 风险分级，非结论
  "signals": [{ "label", "quote", "confidence", "verdict_note" }],
  "contradictions": [{ "nature", "a", "b" }],
  "by_dimension": { "no_embodied_detail": 0.8, /* 五维各 0~1 */ },
  "summary": "存在明显虚构成分，建议谨慎复核。" }
```

## 快速开始

### 单元测试（无依赖、无密钥）

```bash
python -m pytest -v          # 24 tests，用 Mock 驱动，确定性
```

### 可复现的自检（Mock，验证判别性）

```bash
# real（真实经历）→ 低风险；faked（AI 注水）→ 高风险
python scripts/verify.py review tests/fixtures/real.md  tests/fixtures/real_answers.json  --mock --responses tests/fixtures/responses/mock_review_real.json
python scripts/verify.py review tests/fixtures/faked.md tests/fixtures/faked_answers.json --mock --responses tests/fixtures/responses/mock_review_faked.json
```

### 真实模型冒烟（需自备凭证）

按所用模型的官方文档核对 `PRO_MODEL` / `FLASH_MODEL` 准确模型名后：

```bash
API_KEY=sk-... BASE_URL=... PRO_MODEL=... FLASH_MODEL=... \
  python scripts/verify.py review tests/fixtures/real.md tests/fixtures/real_answers.json
```

## 项目结构

```
adverhire/          # 对抗审查引擎库（可测内核）
  machine.py        # AdversarialStateMachine：parse→probe→scrutinize→verdict
  parse.py          # 简历 → 结构化断言
  probe.py          # 坑题生成（针对具体断言植入错误前提）
  followup.py       # 追问判别逻辑（corrected/vague/echoed）
  scrutinize.py     # 虚构成分信号 + 矛盾挖掘
  verdict.py        # 风险分级报告（硬编码不变量：绝不淘汰/录用）
  llm.py            # LLM 抽象（ModelRole：PRO/FLASH + MockLLM 测试桩）
scripts/            # CLI 驱动（probe/review）+ 真实模型冒烟运行器
.skill/adverhire/   # Claude Code Skill（交互皮肤）
tests/              # Mock 驱动的确定性测试 + R1 白盒基线夹具
docs/               # 立项文档、设计 spec、实现计划、docs 罗盘
```

## 路线图

- **Phase 0（进行中）**：核心引擎 + Skill/CLI 形态 + AI 应用开发岗模板
- **Phase 1**：多 Agent 编排、评估模型迭代、覆盖更多技术岗模板
- **Phase 2**：批量核验、企业 API、评估精度优化
- **Phase 3**：微调、插件生态、非技术岗模板、企业私有化部署

## License

[MIT](LICENSE) · © XucroYuri

---

**adverhire — 让招聘回归真实能力** · **hiredetector — 给面试装个测谎仪**
