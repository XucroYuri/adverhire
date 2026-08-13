# adverhire | Adversarial Hiring Agent

> 对抗性招聘智能体·招聘测谎仪

**一句话**：AI 时代，每个求职者都能伪装成"完美候选人"——adverhire 帮面试官把虚假的完美逐层戳穿，还原真实能力。让招聘回归真实能力，让踏实做事的人不被劣币驱逐。

## 时弊：面试正在失效

这不是危言耸听，是正在发生的事实——

- **超 7 成求职者用 AI 优化简历**，项目经历、技术栈、量化指标一键"注水"，光鲜完整到 HR 无从下手。
- **超 4 成在远程面试中用 AI 提词器实时代答**，输出标准化工整、滴水不漏的"完美答案"。
- **传统面试题库、八股提问已全面失效**——你在考他"会不会"，他其实在考你能不能看穿 AI。
- **错配成本极高**：入职后才发现"完美候选人"是张空壳，招聘、培训、离职的多重成本全打了水漂。

而市面上的 AI 招聘工具，几乎全都站在**求职者**那一边——模拟面试、简历润色、刷题助手。
招聘方一侧面对日益精密的 AI 作弊，几乎是裸奔。**攻防的失衡已经到了荒唐的地步。** adverhire
就是来填这个空白的：**给面试装个测谎仪。**

## 解决方案：不靠主观，用对抗性方法系统辨真

我们不做"问得更难"，而是**制造只有真做过的人才会察觉的破绽**。围绕候选人简历的每个
具体断言（一个数值、一个技术选型、一次决策），植入"看似合理但实际错误"的陷阱，看你
是真懂、还是 AI 代答的顺势附和。

- **简历注水 → 逐条可验证断言**，针对具体数值/技术选型植入错误前提，听真实的纠错反应。
- **AI 代答 → 动态追问**，回答含糊就逼问具体到代码数字，顺杆爬就逼问改之前的线上实际。
- **真伪判断 → 五维信号 + 跨源矛盾**，每条判断都带原文证据链，可溯源、可复核。

引擎（`adverhire/*`）是可测的**确定性规则内核**，负责数据、归一化、不变量校验、信号
与风险的规则计算；真正的对抗推理——设计隐蔽坑题、判语义歧义、写总结——由 Claude Code
的 **subagent 实时完成**。**零外部 LLM API 依赖**，能力上限取决于 agent 的共情推理而非
大模型 API。

## 形态

以 **Skill + CLI** 运行在 Claude Code / Codex 等 Agent 框架下——Agent 框架本身是交互壳，
无需自建 Web 工作台。能力内核是可测纯规则引擎，交互推理是 agent 原生循环。

### 作为 Claude Code Skill（推荐）

在 Claude Code 中执行 `/adverhire`，自动加载完整工作流：
1. **抽断言**：读简历，列出可验证断言。
2. **拿战术、设计坑题**：引擎给坑题战术（A1 数值 / A2 技术细节 / A3 决策），实时设计具体问句。
3. **动态追问**：判三态（corrected/vague/echoed），自动分支深挖，最多 3 层。
4. **全程核验**：五维信号 + 跨源矛盾 + 风险分级，带证据链。
5. **解读**：风险分级不是结论，证据链给你看"为什么这么判"。

方法论文档见 `.claude/skills/adverhire/references/adversarial-method.md`。

### 直接命令行（subagent / 脚本接口）

```bash
# 1. 战术：subagent 抽出断言后，引擎归一化 + 给坑题战术
python scripts/verify.py tactics --claims claims.json

# 2. 校验：subagent 设计好坑题后，引擎强制不变量#1（坑题派生自真实断言、非空）
python scripts/verify.py validate --claims claims.json --traps traps.json

# 3. 核验：collect 全部回答后，引擎跑信号/矛盾/风险
python scripts/verify.py review --claims claims.json --answers answers.json --summary "..."
```

`review` 输出结构：

```json
{ "overall": "HIGH",
  "signals": [{ "label": "no_embodied_detail", "quote": "...", "confidence": 0.8, "verdict_note": "..." }],
  "contradictions": [{ "nature": "scale_mismatch", "a": "...", "b": "..." }],
  "by_dimension": { "template_cliche": 0.0, "no_embodied_detail": 0.8, /* 五维各 0~1 */ },
  "summary": "存在明显虚构成分，建议谨慎复核。" }
```

## 两条铁律（硬编码不变量）

1. **坑题永远派生自候选人自述的简历断言**——不提出格、无关、无来源的刁难问题。
2. **绝不输出"淘汰/录用"结论**——只给风险分级 + 证据链，最终判断归人工。

> adverhire 的立场从不含糊：**要戳穿的是"用 AI 伪装成不是自己的那个自己"，而不是人本身。**
> 精准辨真，是为让有真才实学的人脱颖而出。

## 快速开始

```bash
python -m pytest -v    # 纯规则引擎 24+ 测试，确定性全绿
```

### 判别性自检（纯规则，无 LLM）

对 R1 白盒基线跑真实流程：`tests/fixtures/real.md`（真实经历）vs `tests/fixtures/faked.md`（AI 注水）。
预期 real 的回答 `overall` 偏低、signals 少；faked 的回答 `overall` 偏高、signals 多条。
这是全链路的确定性验证，无需任何 API 凭证。

## 项目结构

```
adverhire/           # 确定性规则内核（零 LLM 依赖）
  parse.py           # normalize_claims：断言归一化
  probe.py           # trap_tactics（坑题战术）+ validate_traps（不变量#1）
  scrutinize.py      # detect_signals（五维启发式）+ detect_contradictions
  verdict.py         # grade_risk（风险计分，不变量#2）
  machine.py         # 薄纯函数组合，供 subagent 调用
  followup.py        # classify_answer 三态判别 + 追问纪律
scripts/             # verify.py：subagent 结构化接口（tactics/validate/review）
.claude/skills/adverhire/  # Claude Code Skill（交互皮肤 + 推理协议）
tests/               # 纯规则确定性测试 + R1 白盒基线
docs/                # 立项文档、设计 spec、实现计划、docs 罗盘
```

## 路线图

- **Phase 0（进行中）**：确定性引擎 + Skill/CLI 形态 + AI 应用开发岗模板
- **Phase 1**：多岗模板、信号/矛盾规则调优、agent 推理协议迭代
- **Phase 2**：批量核验、企业 API、判别度打磨
- **Phase 3**：微调、插件生态、非技术岗模板、企业私有化部署

## License

[MIT](LICENSE) · © XucroYuri

---

**adverhire** — 让招聘回归真实能力,给面试装个测谎仪
