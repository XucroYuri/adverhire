# 开源对抗情报 — 求职侧 AI 工具编目与反制

> **用途**:把 ~100 个高星的"AI 简历优化 / AI 面试辅助"开源项目与 SaaS(求职侧 AI)编目为
> adverhire 的**潜在对抗对象**。每个威胁向量不是孤立条目,而是对应一套 adverhire 的反制检测。
> 这是"站在招聘方侧,基于第一性原理 + 对抗性审查全面压制这类 Agent/tool"的情报地基。

---

## 0. 一句话定位

**求职侧 AI 已从"润色"演化为"全流程伪装"**:简历端按 JD 千人千面灌水、面试端用隐形提词器
实时代答、投递端 agent 批量海投。adverhire 的对抗目标不是"某一款工具",而是**这类工具共享的
欺骗模式**——逐个击破会永远追不上,击破模式才能规模压制。

---

## 1. 编目索引(99 个,按类别)

| 类别 | 数量 | 文件 | 代表威胁 |
|------|------|------|----------|
| **AI 简历优化工具**(生成/ATS/JD定制) | 25 | [ai-catalog-resume-tools.md](ai-catalog-resume-tools.md) | reactive-resume(40k)、AIHawk 自动投递+JD改写(30k)、RendererCV、OpenResume |
| **AI 面试辅助工具**(提词器/转写/题库) | 24 | [ai-catalog-interview-assist.md](ai-catalog-interview-assist.md) | cheating-daddy(5.5k)、interview-coder(4.4k)、Cluely/OpenCluely、awesome-behavioral**
| **Skill/Agent 形态**(Claude/Cursor 求职技能) | 26 | [ai-catalog-skills.md](ai-catalog-skills.md) | ai-job-search(31k)、career-ops(64k)、awesome-claude-skills、resume-tailoring-skill |
| **当前市场最强/最新**(SaaS + 新高星) | 24 | [ai-catalog-current-sweep.md](ai-catalog-current-sweep.md) | Cluely/Interview Coder($5.3M 融资)、Final Round、Rezi、Enhancv、Teal**

> 每个文件的"关键能力/核心手法"列记录了"若被用作欺骗,产出什么样的话术/伪装",
> 是反制的输入。

---

## 2. 九大共性欺骗模式 → adverhire 反制(对抗性审查映射)

这是编目的真正价值:把 99 个工具压缩成**可逐一反制的欺骗模式**,并映射到引擎检测。

| # | 共性欺骗模式 | 来源类别代表 | adverhire 反制检测 | 机制 |
|---|--------------|-------------|-------------------|------|
| 1 | **JD 反编译 + 关键词镜像**(逐词对齐岗位要求) | resume/ATS 工具 | `over_alignment`(新增) | 过度对齐=反信号:真经历有缺口与噪声,完美镜像 JD 反而暴露生成痕迹 |
| 2 | **量化指标自动灌水**(补 QPS%/用户数) | resume SaaS(Rezi/Enhancv) | `detect_contradictions`(scale)+ `over_alignment` | 假数字撑不起跨维度一致性;指标对不上项目体量 |
| 3 | **隐形提词器秒答** | interview-assist | `behavioral_uniformity`(新增) | 秒答 + 平滑无挣扎 = 工具代答;真人深挖有认知轨迹 |
| 4 | **无法接续深挖**(浅层答好、深层耗竭) | interview-assist | `detail_exhaustion`(新增) | 追问越深具体密度无法重新接续 = 详情耗竭 |
| 5 | **同一 LLM 风格统一合成**(口径一致话术) | skills 形态 | `idiosyncrasy_absence`(新增) | 多段高出复用 = 单引擎批量生成,无独特性残差 |
| 6 | **STAR/行为面套模板** | awesome-behavioral** | 缺失式中 `over_generalization` + subagent 落锤 | 模板 STAR 无"我的那个事故/私人约束" |
| 7 | **批量海投 + 千人千面** | ApplyPilot/AIHawk | `over_alignment` + HR 侧数量信号(人工) | 同一候选对多岗位的"完美定制"本身就可疑 |
| 8 | **对屏幕共享隐形**(绕过远程面反作弊) | 提词器 | 属行为/屏幕取证域,`behavioral_uniformity` 兜底 | 文本层难直接,靠秒答+无法深挖的间接证据 |
| 9 | **可离线/fork 改私钥**(无第三方日志可查) | skills 形态 | 无固定指纹 → 反制靠**结构性一致性**而非模板库 | 正因无指纹,更要抓"跨维度一致性塌缩" |

---

## 3. 第一性原理:为什么是"一致性塌缩 + 独特性残差"

对抗情报反复印证了一件事:**这些工具都能伪造单点(一句话/数字/关键词),但都不能伪造
"跨深度、跨维度、跨时间线的连贯一致人生"**。

- 工具伪造是"拉局部标准答案/对 JD 反编译",不是"一个连贯的真实经历"。
- 真经历在追问深挖下信息熵单调递增;伪装在深挖下"细节耗竭"。
- 真个人留下"无法被通用生成器独立产生"的独特性残差;AI 趋向信息熵低的平均值。

这正是 `docs/strong-discrimination-framework.md` 的结构性检测(consistency collapse +
detail exhaustion + idiosyncrasy residual + behavioral uniformity)的设计依据。

---

## 4. 反制覆盖状态

| 反制检测 | 实现状态 |
|----------|----------|
| `behavioral_uniformity`(行为流平滑) | ✅ 已实现(`scrutinize.detect_behavioral`) |
| `detail_exhaustion`(深挖耗竭) | ✅ 已实现(`scrutinize.detect_structural`) |
| `idiosyncrasy_absence`(跨段复用) | ✅ 已实现(`scrutinize.detect_structural`) |
| `over_alignment`(JD 过度对齐,模式#1/#2/#7) | ✅ 已实现(`scrutinize.detect_overalignment`,接入 review `--jd`) |
| scale/tech/procedural 矛盾 | ✅ 已实现(`detect_contradictions`) |

> `over_alignment` 以 JD 命名技术词覆盖率 ≥60% 为镜像痕迹信号（AI 按 JD 反编译必然逐字带上
> Redis/Kafka/QPS...，真经历覆盖的是自然子集）。接入 `verify.py review --jd`。

---

## 5. 更新说明

- **采集时间**:2026-08-14。星数为 GitHub API 快照。
- 本目录是"活文档":随着求职侧 AI 演进,新增工具/新欺骗模式应追加对应反制检测。
- 反制采用"击破模式而非逐个追"——新增威胁时先抽象其共性模式,再强化对应结构性检测。
