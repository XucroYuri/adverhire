# AI 求职侧工具现状全景 — 2025-2026 Current Sweep

补全另一次调研缺口的"当前最强/最新"编目。星数为查询时点的 GitHub stargazers_count。
"核心手法"列聚焦:求职者靠它把简历/回答"伪装/包装"成什么样。

| 名称 | 类型 | 网址/仓库 | 核心手法 |
|---|---|---|---|
| Final Round AI (Interview Copilot) | SaaS | https://www.finalroundai.com | 实时面试提词:监听面试音/桌面,把面试官提问转写后即时生成定制答案投影到悬浮窗,并有 AI Resume Builder 按 JD 关键词重写简历、量化灌水 |
| Cluely (原名 Interview Coder, Roy Lee 出品) | SaaS | https://cluely.com | "隐形副驾驶":不可被屏幕共享检测的隐藏答题窗,实时截图/OCR 面试题(尤其 LeetCode DSA),注入 AI 答案;已融资 $530 万,主打过 Amazon/Meta 面试的可隐藏代答 |
| Interview Coder (开源分叉) | OSS | https://github.com/PEAandDA/interview-coder | 隐形桌面应用,截图自动搜题+注入答案;大量分叉(veerawat-s/itc 等),让求职者"零刷题"伪装成手写最优解 |
| Sensei AI (senseicopilot) | SaaS | https://www.senseicopilot.com | 面试实时提词+简历与 Prep 库;编码面试把答案/题解实时推到侧屏,主打"无需准备也能流利答出 STAR" |
| OpenCluely | OSS | https://github.com/TechyCSR/OpenCluely (785★) | 开源 Cluely 替代:隐形悬浮层 + 实时 AI 提示 + 题图智能抓取,专攻 DSA/OA/CP 面试,可本地/自定义模型,绕过屏share |
| GhostMentor | OSS | https://github.com/DressedHuman/GhostMentor | 隐形 AI 侧写:绕过 Zoom/Google Meet 屏幕共享检测注入答案,标榜"cheat-proof interview wingman" |
| Specter-AI | OSS | https://github.com/umairinayat/Specter-AI | 隐私优先 Cluely 替代:透明 always-on-top 悬浮层(屏share不可见)+实时 OCR/音频转写+OpenRouter 流式答题 |
| Pikabaka | OSS | https://github.com/royisme/pikabaka | 开源面试 copilot:实时转写+AI 建议答案+截图推理,BYO key 或 Ollama 本地离线,Mac+Win |
| interview-copilot (innovatorved/realtime) | OSS | https://github.com/innovatorved/realtime-interview-copilot (112★) | 桌面 app 实时音频转写+AI 生成应答,把面试官提问实时转成候选可照读的答案 |
| AI-powered Interview Assistant (Vijaysingh1621) | OSS | https://github.com/Vijaysingh1621/AI-powererd-interview-Assistant (41★) | 接 Google Meet/Zoom,Deepgram 转写(~100ms),从上传简历取上下文(Gemini+Pinecone),用 Claude 生成答案 |
| Rezi | SaaS | https://www.rezi.ai | AI 简历生成:自动扩写项目经历补量化指标(数字/百分比),生成 ATS 关键词密度优化的"标准满分"简历 |
| Enhancv | SaaS | https://enhancv.com | AI bullet generator 把平淡职责改写为带 STAR+量化成果的生动措辞,ATS 解析/关键词匹配评测最高分 |
| resume.io | SaaS | https://resume.io | 海量模板+AI 自动补全要点,把经历一键"优化"为招聘者偏好措辞,弱化真实水平 |
| Kickresume | SaaS | https://www.kickresume.com | AI 生成简历/求职信+GPT 对话式改写,自动套用目标 JD 关键词制造人岗匹配假象 |
| Resume Worded | SaaS | https://resumeworded.com | ATS 打分器:给简历/领英打"通过率/关键词缺失"分,驱动照评分反复灌入关键词和量化改写 |
| Teal | SaaS | https://www.tealhq.com | 简历+求职追踪平台:对每个 JD 自动做匹配评分,输出"量身定制"版简历/求职信(AI Tailor)批量投递 |
| Wobo AI | SaaS | https://www.wobo.ai | "Tinder 式求职"+AI 自动申请:匹配岗位后 AI 代填申请表、代写材料并一键代投,以量取胜制造面试机会 |
| JobHunt Genie / JobHuntr | SaaS | https://www.producthunt.com/products/jobhunt-genie | AI 批量抓岗+自动投递,简历与 Cover Letter 按岗自动生成,"睡觉时替你找工作" |
| ApplyPilot | OSS | https://github.com/Pickle-Pixel/ApplyPilot (1442★) | AI agent 代投:任意网站任意表单自动填写、自动生成简历材料并提交,量产定制化申请 |
| LinkedIn-AI-Job-Applier-Ultimate | OSS | https://github.com/beatwad/LinkedIn-AI-Job-Applier-Ultimate (147★) | Playwright 自动投 LinkedIn/Indeed,给每个岗位生成定制简历,数据匿名化+Telegram 上报,规避封号批量投递 |
| AutoApply (Liam-Frost) | OSS | https://github.com/Liam-Frost/AutoApply (111★) | AI 求职 agent:岗位发现+匹配打分+量身生成材料+自动填表(人工 final 提交),包装人岗匹配的真实感 |
| AutoApply AI Agentic (Rayyan9477) | OSS | https://github.com/Rayyan9477/AutoApply-AI-Agentic-Browser-Automation-for-Job-Search (65★) | 浏览器自动化抓岗 + AI 定制简历/求职信 + 自动提交申请,规模化"千人千面"投递 |
| ResumeSkills | OSS | https://github.com/Paramchoudhary/ResumeSkills (1624★) | Claude Code 简历优化 agent 技能集:自动 ATS 优化、resume-quantifier 把经历补量化数字、面试 prep |
| job-hunter (wexxwuther) | OSS | https://github.com/wexxwuther/job-hunter | 开源 AI skill:搜 LinkedIn/Indeed/州板,给岗位打 1-5 真实度分,输出针对性 ATS 简历+求职信(在 Claude Code/Codex 跑) |
| 01GOD/An-AI-coding-assistant-for-leetcode | OSS | https://github.com/01GOD/An-AI-coding-assistant-for-leetcode-practice | LeetCode 练习侧 AI 辅助:自动解题/题解注入,训练/伪装成能秒切算法题的候选 |

---

## 2025-2026 年求职侧 AI 演进的共性趋势

(≤150 字)

求职侧 AI 已从"润色"演化为"全流程伪装":简历端由关键词灌水、量化指标自动补全升级为**按 JD 千人千面自动生成 ATS 满分材料**;面试端由静态模拟升级为**不可被屏幕/录屏检测的隐形实时代答**(OCR 截题+流式投屏答案);投递端出现**agent 化批量代投**。核心从"包装经历"转向"替代本人表现",对抗难度从文案检测升级到行为/屏幕取证。
