# AI 简历优化工具对抗情报编目 (Adversarial Catalog: AI Resume Tools)

> 用途:站在招聘方(`adverhire`)侧,识别求职者可能用来 AI 注水简历的高星开源工具。`关键能力`列描述"若被用作欺骗,产出何种注水内容",直接对接 `adverhire` 的 `detect_contradictions` / 量化指标核验逻辑。
> 数据采集:GitHub Search API (gh CLI),星数采集时间 2026-08-14。

## 编目

| 名称 | 星数 | 仓库/URL | 类型(生成/优化/ATS) | 关键能力(求职者能怎么用 AI 伪装) |
|------|------|----------|---------------------|-----------------------------------|
| reactive-resume | 40,339 | https://github.com/amruthpillai/reactive-resume | 生成 | 开源自定义简历编辑器,可批量套模板 + 填内容,配合 LLM 生成大量"完美排版"的注水简历,统一话术掩盖人工痕迹 |
| Auto_Jobs_Applier_AIHawk | 30,174 | https://github.com/feder-cr/Auto_Jobs_Applier_AIHawk | 优化 | 针对每个职位 URL 自动改写简历/求职信以"精准对齐 JD",可系统性植入职位关键词、编造匹配经验,绕过 ATS 关键词过滤 |
| RenderCV | 17,356 | https://github.com/rendercv/rendercv | 生成 | 从 YAML 一键生成学术/工程简历,支持注入任意虚构项目与指标,产物 LaTeX/PDF 高度"规范",难以人工辨别真伪 |
| OpenResume | 8,834 | https://github.com/xitanggg/open-resume | 生成/解析 | 简历建造器 + 解析器,可生成 ATS 友好 HTML 简历并回测解析,帮求职者反推"ATS 爱读什么"再填充虚化内容 |
| resume-cli (jsonresume) | 4,718 | https://github.com/jsonresume/resume-cli | 生成 | JSON Schema 标准化简历,支持以代码/模板批量生成,便于程序化生成大量同源、风格一致的注水简历 |
| oh-my-cv | 1,050 | https://github.com/Renovamen/oh-my-cv | 生成 | 本地 Markdown 简历生成器,支持自定义与多模板,可快速产出界面精致的伪造简历 |
| resume-builder (sadanandpai) | 1,216 | https://github.com/sadanandpai/resume-builder | 生成 | 标准单页简历在线建造器,拖拽式编辑,快速搭出"标准专业"外壳后套用 AI 文案 |
| resumecards | 739 | https://github.com/ellekasai/resumecards | 生成 | Markdown 简历生成器,移动端/桌面自适应,轻量产出可用作批量投递的注水简历载体 |
| markdown-resume | 654 | https://github.com/junian/markdown-resume | 生成/ATS | 强调"ATS + 人读"双友好 Markdown 简历,内置 ATS 优化套路,引导求职者堆砌关键词与指标 |
| resumed | 550 | https://github.com/rbardini/resumed | 生成 | 轻量 JSON Resume 构造器,纯数据驱动,可脚本化批量产出同构简历,便于绕过人工甄别 |
| resume-builder (sramezani) | 499 | https://github.com/sramezani/resume-builder | 生成 | 实时设计、100% 免费在线建造器,快速生成可下载注水简历 |
| resuminator | 492 | https://github.com/resuminator/resuminator | 生成 | 拖拽式简历建造器,易产出一致化、模板化的"完美简历",掩饰真实的零散经历 |
| resume_render_from_job_description (AIHawk) | 413 | https://github.com/feder-cr/resume_render_from_job_description | 优化 | 抓取职位页(URL)自动定制简历与求职信,精准对齐 JD 技能与措辞,可捏造不存在的"项目经历与技能匹配" |
| blopa/Resume-Builder | 246 | https://github.com/blopa/Resume-Builder | 生成 | 免费开源简历建造器,自由维护任意简历内容,可作为注水内容的快速投放工具 |
| lib_resume_builder_AIHawk | 193 | https://github.com/feder-cr/lib_resume_builder_AIHawk | 优化 | AIHawk 简历定制核心库,提供按 JD 重写简历/求职信的底层能力,可被复用做规模化关键词注水 |
| javiera-vasquez/claude-code-job-tailor | 167 | https://github.com/javiera-vasquez/claude-code-job-tailor | 优化 | Claude Code 简历优化系统,解析 JD、按优先级排序要求、自动挑选"最相关成就",可无限生成针对不同职位的定制 PDF,内容易注水 |
| tonykipkemboi/resume-optimization-crew | 153 | https://github.com/tonykipkemboi/resume-optimization-crew | 优化 | CrewAI 多 Agent 简历优化,分析 JD、打分匹配并给定制改进,可生成"高分对齐 JD"的虚化项目描述 |
| anurag3407/career-pilot | 126 | https://github.com/anurag3407/career-pilot | 优化 | AI 职业平台(简历优化/模拟面试),提供自动优化的注水文案与话术,弱化人工痕迹 |
| espin086/GPT-Jobhunter | 93 | https://github.com/espin086/GPT-Jobhunter | 优化 | 上传一次简历即可批量按目标岗位"自动重写整份简历"来绕过 ATS,系统性伪造匹配度 |
| resume-optimization (mhbuehler) | 16 | https://github.com/mhbuehler/resume-optimizer | 优化/ATS | NLP 工具计算简历与 JD 相似度并抽取技能,帮求职者补齐缺口关键词、伪装技能匹配 |
| seehiong/ats-buddy | 73 | https://github.com/seehiong/ats-buddy | ATS | 本地 ATS 分析器(WebLLM/Ollama),给出匹配分/缺失关键词/重写建议,求职者据此反向填充 ATS 想要的关键词 |
| Azoo92i/AutoApplyMax | 58 | https://github.com/Azoo92i/AutoApplyMax | 生成/优化/ATS | Chrome 扩展:LinkedIn/Indeed 自动投递 + AI 简历生成 + ATS 评分,可实现规模化海投 + 注水简历生成 |
| karthikrshet/Career-Agents | 35 | https://github.com/karthikrshet/Career-Agents | 优化/ATS | 167 个 AI Agent 的"ATS 简历工作室",全面自动优化简历措辞与关键词,掩盖真实经历 |
| resume-ai (resume-llm) | 392 | https://github.com/resume-llm/resume-ai | 生成 | 本地隐私简历构建器,LLM + Markdown 生成 ATS 就绪 DOCX,可产出高度专业化的注水文档 |
| cover-letter-ai (Ancastal) | 8 | https://github.com/Ancastal/Cover-Letter.AI | 生成 | 抓取职位 URL + LLM 生成个性化求职信,可批量编造"热情 + 匹配"的套话,配合简历同源造假 |

## 这类工具的共性伪装模式 (≤150 字)

> 这批工具共同指向"JD 反编译 + 关键词镜像 + 指标话术填充"三位一体的注水范式:求职者上传 JD,工具解析出 ATS 想要的技能关键词与优先级,再批量改写简历/求职信以逐词对齐,并自动补造"量化指标"(如"提升 QPS X%""降低延迟 Y%")和标准化项目经历。产物排版规范、措辞完美、匹配度高,几乎无拼写/语法缺陷——而这"过度一致、过度对齐、过度量化"恰是 `adverhire` 可检测的反向信号:真实经历往往有缺口与噪声,完美镜像 JD 反而暴露生成痕迹。
