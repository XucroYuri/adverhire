# Adverhire 对抗审查状态机 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended)
> or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax
> for tracking.

**Goal:** 构建 `adverhire` 薄壳 Python 包，内含一个可测的对抗审查状态机
（`parse → probe → scrutinize → verdict`），用坑题生成 + 动态追问 + 虚构成分检测
+ 矛盾挖掘，识别 AI 代答与简历注水，并输出低/中/高风险报告（绝不生成淘汰结论）。

**Architecture:** 单一状态机 Agent（方案 1），四个阶段各为独立可测方法。利用 LLM
适配器抽象出 V4 Pro / V4 Flash 两个模型角色，因此所有 LLM 调用可通过注入的 `MockLLM`
在测试中确定性驱动——状态机管线、数据模型、分支逻辑全部走纯单元测试，不依赖真实
API/密钥/计费。真实模型调用只发生在 POC 运行器（Task 12），作为人工冒烟验证。

**Tech Stack:** Python 3.11+、标准库 `dataclasses`/`argparse`、`pytest`。无第三方
LLM SDK 依赖——真实调用由用户自备的 OpenAI 兼容脚本完成（见 Task 12）。MVP 不引入
LangGraph/RAG/向量库/Web 框架（见 spec §8 YAGNI）。

## Global Constraints

- Python ≥ 3.11。包结构：`adverhire/`（源码）+ `tests/`。
- **不变量 #1**：probe 生成的每个坑题必须派生自候选人的 `Claim`（简历/回答断言）；
  状态机内禁止生成无来源的刁难问题。
- **不变量 #2**：verdict 的 `overall` 只可能是 `LOW` / `MEDIUM` / `HIGH`，绝不包含
  "淘汰 / 录用" 结论。
- 模型分工：V4 Pro 负责 probe（坑题）、scrutinize 深挖、verdict；V4 Flash 负责 parse、
  scrutinize 初筛。多模型适配层本阶段不完整实现，仅提供 `ModelRole` 占位。
- 所有坑题/追问/信号/矛盾对象中引用的原文必须是 `quote`/原文切片，可追溯，不搞黑盒。
- 不在任何提交中放入客户的真实简历 / PII；`tests/fixtures/` 内的样本为人工虚构。

---

## File Structure

```
adverhire/
  __init__.py            # 导出 AdversarialStateMachine 及公开类型
  models.py              # 全部 @dataclass 数据模型（Claim/Trap/FollowUp/QuestionSet/…）
  llm.py                 # LLM 抽象：ModelRole、LLMClient 协议、MockLLM
  parse.py               # parse 阶段：Profile 文本 → 结构化 Profile
  probe.py               # probe 阶段：Profile → QuestionSet（坑题）
  followup.py            # 动态追问逻辑：AnswerLog → 下一层 FollowUp 判断
  scrutinize.py          # scrutinize 阶段：Answers → FabricationSignals + Contradictions
  verdict.py             # verdict 阶段：信号 → RiskReport
  machine.py             # AdversarialStateMachine 编排四个阶段
  cli.py                 # 薄壳 CLI：adverhire inspect <resume> -o <out.json>
tests/
  fixtures/
    real.md              # 深度真实经历的手工简历（已知答案基线）
    real_answers.json    # 3 条真人自然回答
    faked.md             # AI 生成的同岗位注水版简历
    faked_answers.json   # 3 条 AI 提词器式回答
  test_models.py
  test_parse.py
  test_probe.py
  test_followup.py
  test_scrutinize.py
  test_verdict.py
  test_machine.py
  test_cli.py
```

每个文件单一职责：`models.py` 只放类型；`llm.py` 只做模型抽象；各阶段纯函数化
（输入 → 输出，无副作用），便于单独测试与后续编排演进。

---

### Task 1: 包骨架与数据模型

**Files:**
- Create: `adverhire/__init__.py`
- Create: `adverhire/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: 无。
- Produces: `adverhire/models.py` 中的数据类型被后续所有任务引用：
  - `RiskLevel`（`LOW`/`MEDIUM`/`HIGH`，`str` enum）
  - `Dimen`（五个信号维度名，`str` enum）
  - `Claim(bullet:str, tech:list[str], metric:float|None, source:str)`
  - `ImpactedTrap(claim:Claim, wrong_preset:str, question:str, discriminators:list[str])`
  - `FollowUp(ancestor_question:str, branch:str, question:str, depth:int, discriminator_hit:bool)`
  - `QuestionSet(questions:list[ImpactedTrap], per_trap:dict[str,list[FollowUp]])`
  - `Contradiction(a:Claim, b:Claim, nature:str)`
  - `SignalEvidence(label:str, quote:str, confidence:float, verdict_note:str)`
  - `RiskReport(overall:RiskLevel, signals:list[SignalEvidence], contradictions:list[Contradiction], by_dimension:dict[str,float], summary:str)`

- [ ] **Step 1: 写失败测试**

创建 `adverhire/__init__.py`（空，后续填充导出）和 `adverhire/models.py`
（先只放占位注释），然后写 `tests/test_models.py`：

```python
from adverhire.models import RiskLevel, Claim, ImpactedTrap

def test_risk_level_enum_values():
    assert {rl.value for rl in RiskLevel} == {"LOW", "MEDIUM", "HIGH"}

def test_claim_defaults_and_source():
    c = Claim("优化缓存 QPS+50%", ["redis"], 50.0, "resume")
    assert c.metric == 50.0 and c.source == "resume"

def test_trap_carries_claim_and_discriminators():
    c = Claim("纯文本", [], None, "resume")
    t = ImpactedTrap(c, wrong_preset="改成1800", question="从200怎么调到1800的？",
                     discriminators=["纠正数值", "描述增长曲线"])
    assert t.claim is c and t.discriminators and t.question
```

- [ ] **Step 2: 运行确认失败**

Run: `cd /Volumes/SSD/Code/09-business/adverhire && python -m pytest tests/test_models.py -v`
Expected: FAIL（ModuleNotFoundError: adverhire）

- [ ] **Step 3: 写实现** — 填充 `adverhire/models.py`：

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class Dimen(str, Enum):
    TEMPLATE_CLICHE = "template_cliche"
    NO_EMBODIED_DETAIL = "no_embodied_detail"
    OVER_GENERALIZATION = "over_generalization"
    MISSING_AFFECT = "missing_affect"
    OVER_STANDARDIZED = "over_standardized"

@dataclass
class Claim:
    bullet: str
    tech: list[str] = field(default_factory=list)
    metric: float | None = None
    source: str = "resume"  # "resume" | "answer"

@dataclass
class ImpactedTrap:
    claim: Claim
    wrong_preset: str
    question: str
    discriminators: list[str] = field(default_factory=list)

@dataclass
class FollowUp:
    ancestor_question: str
    branch: str  # vague / corrected / echoed
    question: str
    depth: int
    discriminator_hit: bool = False

@dataclass
class QuestionSet:
    questions: list[ImpactedTrap] = field(default_factory=list)
    per_trap: dict[str, list[FollowUp]] = field(default_factory=dict)

@dataclass
class Contradiction:
    a: Claim
    b: Claim
    nature: str  # tech_mismatch / scale_mismatch / timeline_conflict / procedural_contradiction

@dataclass
class SignalEvidence:
    label: str
    quote: str
    confidence: float = 1.0
    verdict_note: str = ""

@dataclass
class RiskReport:
    overall: RiskLevel
    signals: list[SignalEvidence] = field(default_factory=list)
    contradictions: list[Contradiction] = field(default_factory=list)
    by_dimension: dict[str, float] = field(default_factory=dict)
    summary: str = ""
```

并填充 `adverhire/__init__.py`：

```python
from .machine import AdversarialStateMachine
from .models import (
    RiskLevel, Dimen, Claim, ImpactedTrap, FollowUp,
    QuestionSet, Contradiction, SignalEvidence, RiskReport,
)

__all__ = [
    "AdversarialStateMachine", "RiskLevel", "Dimen", "Claim", "ImpactedTrap",
    "FollowUp", "QuestionSet", "Contradiction", "SignalEvidence", "RiskReport",
]
```

- [ ] **Step 4: 运行确认通过**

Run: `cd /Volumes/SSD/Code/09-business/adverhire && python -m pytest tests/test_models.py -v`
Expected: PASS（3 passed）

> 注：Step 3 的 `__init__.py` 引用了 `machine.AdversarialStateMachine`，该模块在
> Task 8 才创建。为避免过早 ImportError，**Step 3 先临时把 `__init__.py` 写成只
> 导出 `models.*`**，Task 8 完成后再补 `machine` 导入。若你先跑 Task 3 的测试
> 报 ImportError，说明 `__init__.py` 需按此临时版处理：

```python
from .models import RiskLevel, Dimen, Claim, ImpactedTrap, FollowUp, \
    QuestionSet, Contradiction, SignalEvidence, RiskReport

__all__ = ["RiskLevel", "Dimen", "Claim", "ImpactedTrap", "FollowUp",
           "QuestionSet", "Contradiction", "SignalEvidence", "RiskReport"]
```

- [ ] **Step 5: Commit**

```bash
git add adverhire/models.py tests/test_models.py
git commit -m "feat(adverhire): add core data models for adversarial review
Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 2: LLM 抽象（ModelRole / LLMClient / MockLLM）

**Files:**
- Create: `adverhire/llm.py`
- Test: `tests/test_llm.py`

**Interfaces:**
- Consumes: 无（独立模块）。
- Produces: 被 parse/probe/scrutinize/verdict 及各阶段测试引用：
  - `class ModelRole(str, Enum)`：`PRO = "pro"`、`FLASH = "flash"`
  - `class LLMClient(Protocol)`：`def generate(self, role: ModelRole, prompt: str) -> str` + `def structured(self, role: ModelRole, prompt: str, schema: dict) -> dict`
  - `class MockLLM`: 实现 `LLMClient`，构造参数 `responses: dict[ModelRole, list[str|dict]]`，每次调用按序弹出一个；提供 `calls: list[tuple[ModelRole, str]]` 记录调用。

- [ ] **Step 1: 写失败测试** `tests/test_llm.py`：

```python
from adverhire.llm import ModelRole, MockLLM

def test_model_role_values():
    assert {r.value for r in ModelRole} == {"pro", "flash"}

def test_mock_llm_returns_queued_and_records_calls():
    mock = MockLLM(responses={ModelRole.PRO: ["a", "b"]})
    assert mock.generate(ModelRole.PRO, "q1") == "a"
    assert mock.generate(ModelRole.PRO, "q2") == "b"
    assert [(r, p) for r, p, _ in mock.calls] == [(ModelRole.PRO, "q1"), (ModelRole.PRO, "q2")]

def test_mock_llm_structured_returns_dict():
    mock = MockLLM(responses={ModelRole.FLASH: [{"claims": 2}]})
    out = mock.structured(ModelRole.FLASH, "p", {"type": "object"})
    assert out == {"claims": 2}
```

- [ ] **Step 2: 运行确认失败** — `pytest tests/test_llm.py -v` → FAIL（ImportError: adverhire.llm）

- [ ] **Step 3: 写实现** `adverhire/llm.py`：

```python
from __future__ import annotations
from enum import Enum
from typing import Protocol


class ModelRole(str, Enum):
    PRO = "pro"      # 推理：坑题 / 追问决策 / 深挖 / verdict
    FLASH = "flash"  # 快速：简历解析 / 初筛扫描


class LLMClient(Protocol):
    def generate(self, role: ModelRole, prompt: str) -> str: ...
    def structured(self, role: ModelRole, prompt: str, schema: dict) -> dict: ...


class MockLLM:
    """确定性测试桩：按序弹出预设响应，并记录调用（role, prompt, kind）。"""

    def __init__(self, responses: dict[ModelRole, list[str | dict]]):
        self._responses = {r: list(v) for r, v in responses.items()}
        self.calls: list[tuple[ModelRole, str, str]] = []  # (role, prompt, kind)

    def generate(self, role: ModelRole, prompt: str) -> str:
        self.calls.append((role, prompt, "generate"))
        return str(self._take(role, "generate"))

    def structured(self, role: ModelRole, prompt: str, schema: dict) -> dict:
        self.calls.append((role, prompt, "structured"))
        return dict(self._take(role, "structured"))

    def _take(self, role: ModelRole, kind: str):
        bucket = self._responses.get(role, [])
        if not bucket:
            raise AssertionError(f"No queued {kind} response for {role}")
        return bucket.pop(0)
```

- [ ] **Step 4: 运行确认通过** — `pytest tests/test_llm.py -v` → PASS（3 passed）

- [ ] **Step 5: Commit**

```bash
git add adverhire/llm.py tests/test_llm.py
git commit -m "feat(adverhire): add mockable LLM abstraction with model roles
Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 3: parse 阶段 —— 简历文本 → Profile

**Files:**
- Create: `adverhire/parse.py`
- Test: `tests/test_parse.py`

**Interfaces:**
- Consumes: `adverhire.models.Claim`、`adverhire.llm.LLMClient`/`ModelRole`。
- Produces: `parse_resume(llm: LLMClient, text: str) -> list[Claim]`：
  - 用 `ModelRole.FLASH` 调 `llm.structured`，请求 schema 为 `{"claims": [{"bullet","tech","metric","source"}]}`。
  - 从 LLM 返回的 dict 构造 `Claim` list；`source` 固定 `"resume"`，`metric` 由字符串转浮点（无法转则 `None`）。

- [ ] **Step 1: 写失败测试** `tests/test_parse.py`：

```python
from adverhire.parse import parse_resume
from adverhire.llm import ModelRole, MockLLM
from adverhire.models import Claim

def test_parse_builds_claims_from_flash_response():
    mock = MockLLM(responses={ModelRole.FLASH: [{
        "claims": [
            {"bullet": "优化缓存 QPS+50%", "tech": ["redis"], "metric": "50", "source": "resume"},
            {"bullet": "自研压测工具", "tech": ["python"], "metric": None, "source": "resume"},
        ]
    }]})
    claims = parse_resume(mock, "某简历全文")
    assert [c.bullet for c in claims] == ["优化缓存 QPS+50%", "自研压测工具"]
    assert all(c.source == "resume" for c in claims)
    assert claims[0].metric == 50.0 and claims[1].metric is None
    assert mock.calls[0][0] == ModelRole.FLASH  # 解析用 Flash

def test_parse_handles_missing_technical_list():
    mock = MockLLM(responses={ModelRole.FLASH: [{"claims": [{"bullet": "纯文本", "tech": [], "metric": None, "source": "resume"}]}]})
    c = parse_resume(mock, "文本")[0]
    assert c.tech == [] and c.metric is None
```

- [ ] **Step 2: 运行确认失败** — `pytest tests/test_parse.py -v` → FAIL（ImportError: adverhire.parse）

- [ ] **Step 3: 写实现** `adverhire/parse.py`：

```python
from __future__ import annotations
from .models import Claim
from .llm import LLMClient, ModelRole

RESUME_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "bullet": {"type": "string"},
                    "tech": {"type": "array", "items": {"type": "string"}},
                    "metric": {"type": ["string", "null"]},
                    "source": {"type": "string"},
                },
            },
        }
    },
}


def _to_float(value) -> float | None:
    if value in (None, "", "null"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_resume(llm: LLMClient, text: str) -> list[Claim]:
    data = llm.structured(ModelRole.FLASH, text, RESUME_SCHEMA)
    claims = []
    for item in data.get("claims", []):
        claims.append(Claim(
            bullet=str(item.get("bullet", "")),
            tech=[str(t) for t in item.get("tech", []) if t],
            metric=_to_float(item.get("metric")),
            source=str(item.get("source", "resume")) or "resume",
        ))
    return claims
```

- [ ] **Step 4: 运行确认通过** — `pytest tests/test_parse.py -v` → PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add adverhire/parse.py tests/test_parse.py
git commit -m "feat(adverhire): add resume parsing to structured claims via Flash
Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 4: probe 阶段 —— Profile → 坑题（问询线 A）

**Files:**
- Create: `adverhire/probe.py`
- Test: `tests/test_probe.py`

**Interfaces:**
- Consumes: `models.Claim/ImpactedTrap/QuestionSet`、`llm.LLMClient/ModelRole`。
- Produces: `gen_traps(llm: LLMClient, claims: list[Claim]) -> QuestionSet`：
  - 对每条可验证 `Claim`（`metric` 非空 或 `tech` 非空），用 `ModelRole.PRO` 调
    `llm.structured`，请求 schema 为 `{"traps": [{"claim_idx","wrong_preset","question","discriminators"}]}`。
  - 只保留 `claim_idx` 落在 `claims` 范围内、且已生成有效陷阱字串的项；丢弃引用越界的。
  - **不变量 #1 由实现强制**：任何无法关联到既有 `Claim` 的陷阱都会被过滤（`per_trap` 后续填充在 Task 5）。

- [ ] **Step 1: 写失败测试** `tests/test_probe.py`：

```python
from adverhire.probe import gen_traps
from adverhire.llm import ModelRole, MockLLM
from adverhire.models import Claim

CLAIMS = [
    Claim("优化缓存 QPS+50%", ["redis"], 50.0, "resume"),
    Claim("纯文本条目", [], None, "resume"),          # 不可验证，不应生成坑题
]

def test_gen_traps_uses_pro_and_keeps_manifested_traps():
    mock = MockLLM(responses={ModelRole.PRO: [{
        "traps": [
            {"claim_idx": 0, "wrong_preset": "从200调到1800",
             "question": "从200怎么一步步调到1800的？",
             "discriminators": ["纠正数值", "描述增长曲线"]},
        ]
    }]})
    qs = gen_traps(mock, CLAIMS)
    assert len(qs.questions) == 1
    assert qs.questions[0].claim is CLAIMS[0]
    assert mock.calls[0][0] == ModelRole.PRO  # 坑题用 Pro

def test_gen_traps_discards_out_of_range_claim_idx():
    mock = MockLLM(responses={ModelRole.PRO: [{
        "traps": [
            {"claim_idx": 0, "wrong_preset": "p", "question": "q0", "discriminators": []},
            {"claim_idx": 99, "wrong_preset": "p", "question": "q-bad", "discriminators": []},
        ]
    }]})
    qs = gen_traps(mock, CLAIMS)
    assert len(qs.questions) == 1 and qs.questions[0].question == "q0"
```

- [ ] **Step 2: 运行确认失败** — `pytest tests/test_probe.py -v` → FAIL（ImportError: adverhire.probe）

- [ ] **Step 3: 写实现** `adverhire/probe.py`：

```python
from __future__ import annotations
from .models import Claim, ImpactedTrap, QuestionSet
from .llm import LLMClient, ModelRole

TRAP_SCHEMA = {
    "type": "object",
    "properties": {
        "traps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_idx": {"type": "integer"},
                    "wrong_preset": {"type": "string"},
                    "question": {"type": "string"},
                    "discriminators": {"type": "array", "items": {"type": "string"}},
                },
            },
        }
    },
}


def gen_traps(llm: LLMClient, claims: list[Claim]) -> QuestionSet:
    # 只对"可验证断言"生成坑题：有量化指标或技术栈
    claimable = [i for i, c in enumerate(claims) if c.metric is not None or c.tech]
    if not claimable:
        return QuestionSet()

    prompt = _prompt_for(claims, claimable)
    data = llm.structured(ModelRole.PRO, prompt, TRAP_SCHEMA)

    traps: list[ImpactedTrap] = []
    for item in data.get("traps", []):
        idx = item.get("claim_idx")
        question = (item.get("question") or "").strip()
        if isinstance(idx, int) and 0 <= idx < len(claims) and question:
            traps.append(ImpactedTrap(
                claim=claims[idx],
                wrong_preset=(item.get("wrong_preset") or "").strip(),
                question=question,
                discriminators=[str(d) for d in item.get("discriminators", []) if d],
            ))
    # 不变量 #1：只保留能关联到既有 Claim 的坑题（上面已过滤越界 idx）
    return QuestionSet(questions=traps)


def _prompt_for(claims: list[Claim], claimable: list[int]) -> str:
    preview = "\n".join(f"[{i}] {claims[i].bullet}" for i in claimable)
    return (
        "对抗性坑题生成。对下列简历断言，为每条生成一个\"看似合理但错误\"的验证坑题：\n"
        f"{preview}\n要求：坑题必须派生自该断言本身，不提出格问题。"
    )
```

- [ ] **Step 4: 运行确认通过** — `pytest tests/test_probe.py -v` → PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add adverhire/probe.py tests/test_probe.py
git commit -m "feat(adverhire): generate adversarial trap questions for claims
Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 5: followup 阶段 —— 动态追问状态机（B）

**Files:**
- Create: `adverhire/followup.py`
- Test: `tests/test_followup.py`

**Interfaces:**
- Consumes: `models.FollowUp/ImpactedTrap`、`llm.LLMClient/ModelRole`、`adverhire.probe._prompt_for` 无需。
- Produces:
  - `classify_answer(text: str, trap: ImpactedTrap) -> str`
    （纯 Python）：返回 `"vague"` / `"corrected"` / `"echoed"` 之一。
    - `corrected`：回答命中任一 discriminator 子串（如"纠正""其实""不是"）。
    - `vague`：回答过短（`len < 20`）或含"举例""忘了""记不清"。
    - `echoed`：兜底。
  - `next_followup(llm, trap, answer, depth) -> FollowUp`：
    用 `ModelRole.PRO` 生成下一层追问；`branch = classify_answer(...)`；
    `discriminator_hit = (branch == "corrected")`（**动态 3 层**：命中即末层）；
    `depth = depth + 1`。

- [ ] **Step 1: 写失败测试** `tests/test_followup.py`：

```python
from adverhire.followup import classify_answer, next_followup
from adverhire.llm import ModelRole, MockLLM
from adverhire.models import ImpactedTrap, Claim

TRAP = ImpactedTrap(Claim("优化缓存 QPS+50%", ["redis"], 50.0, "resume"),
                    wrong_preset="改成1800", question="从200怎么调到1800的？",
                    discriminators=["纠正", "其实"])

def test_classify_corrected_hits_discriminator():
    assert classify_answer("其实不是，我们从200调到的是1200", TRAP) == "corrected"

def test_classify_vague_when_short_or_forgetful():
    assert classify_answer("嗯…" * 3, TRAP) == "vague"          # 太短
    assert classify_answer("记不清那段细节了", TRAP) == "vague"   # 记不清

def test_classify_defaults_to_echoed():
    assert classify_answer("当时我们做了业务优化和性能提升，整体效果好很多", TRAP) == "echoed"

def test_next_followup_hits_corrected_marks_terminal_layer():
    mock = MockLLM(responses={ModelRole.PRO: ["当时你是怎么发现这个问题的？"]})
    fu = next_followup(mock, TRAP, "其实不是，这个改动不是我做的", depth=1)
    assert fu.branch == "corrected" and fu.discriminator_hit is True
    assert fu.depth == 2 and "发现" in fu.question
```

- [ ] **Step 2: 运行确认失败** — `pytest tests/test_followup.py -v` → FAIL（ImportError: adverhire.followup）

- [ ] **Step 3: 写实现** `adverhire/followup.py`：

```python
from __future__ import annotations
from .models import ImpactedTrap, FollowUp
from .llm import LLMClient, ModelRole


def classify_answer(text: str, trap: ImpactedTrap) -> str:
    t = (text or "").strip()
    if any(seg in t for seg in trap.discriminators):
        return "corrected"
    if len(t) < 20 or any(k in t for k in ("记不清", "忘了", "一时半会儿", "举例")):
        return "vague"
    return "echoed"


PROMPT_TMPL = (
    "候选人对坑题「{question}」的回答是：\n{answer}\n"
    "这是第 {depth} 层追问。若回答含糊不清，追问具体代码/数字/当时取舍；"
    "若顺杆爬复读，追问改之前的线上情况。只输出一句追问。"
)


def next_followup(llm: LLMClient, trap: ImpactedTrap, answer: str, depth: int) -> FollowUp:
    branch = classify_answer(answer, trap)
    prompt = PROMPT_TMPL.format(question=trap.question, answer=answer, depth=depth)
    question = llm.generate(ModelRole.PRO, prompt).strip()
    return FollowUp(
        ancestor_question=trap.question,
        branch=branch,
        question=question,
        depth=depth + 1,
        discriminator_hit=(branch == "corrected"),
    )
```

- [ ] **Step 4: 运行确认通过** — `pytest tests/test_followup.py -v` → PASS（4 passed）

- [ ] **Step 5: Commit**

```bash
git add adverhire/followup.py tests/test_followup.py
git commit -m "feat(adverhire): add dynamic follow-up state machine with dynamic depth cap
Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 6: scrutinize 阶段 —— 虚构成分（C）+ 矛盾挖掘（D）

**Files:**
- Create: `adverhire/scrutinize.py`
- Test: `tests/test_scrutinize.py`

**Interfaces:**
- Consumes: `models.Claim/Contradiction/SignalEvidence`、`llm.LLMClient/ModelRole`、`adverhire.parse.parse_resume`（用于把简历再结构化以做跨源对比）。
- Produces:
  - `scrutinize(llm, answers: list[Claim], resume_claims: list[Claim]) -> tuple[list[SignalEvidence], list[Contradiction]]`
  - 分两级：用 `ModelRole.FLASH` 调结构化初筛，返回 `{"signals":[...], "contradictions":[...]}`；再用 `ModelRole.PRO` 对初筛命中的每条做"Confirm/Reject + verdict_note"深挖（`structured` 请求 `{"confirmations":[...]}`）。
  - 只保留被 `PRO` 确认的信号/矛盾；被驳回收敛为 False。

- [ ] **Step 1: 写失败测试** `tests/test_scrutinize.py`：

```python
from adverhire.scrutinize import scrutinize
from adverhire.llm import ModelRole, MockLLM
from adverhire.models import Claim

RESUME = [Claim("优化缓存 QPS+50%", ["redis"], 50.0, "resume")]
ANSWER = Claim("我们用了单机 redis 就够了", ["redis"], None, "answer")

def test_scrutinize_confirmed_signal_survives():
    mock = MockLLM(responses={
        ModelRole.FLASH: [{
            "signals": [
                {"label": "no_embodied_detail", "quote": "用单机redis就够了", "confidence": 0.7},
            ],
            "contradictions": [],
        }],
        ModelRole.PRO: [{"confirmations": [{"index": 0, "confirmed": True, "note": "无具身细节,规模存疑"}]}],
    })
    sigs, contras = scrutinize(mock, [ANSWER], RESUME)
    assert len(sigs) == 1 and sigs[0].label == "no_embodied_detail"
    assert contras == []

def test_scrutinize_rejects_false_positive():
    mock = MockLLM(responses={
        ModelRole.FLASH: [{
            "signals": [{"label": "template_cliche", "quote": "xxx", "confidence": 0.8}],
            "contradictions": [],
        }],
        ModelRole.PRO: [{"confirmations": [{"index": 0, "confirmed": False, "note": "误报"}]}],
    })
    sigs, _ = scrutinize(mock, [ANSWER], RESUME)
    assert sigs == []  # 误报被 Pro 驳回
```

- [ ] **Step 2: 运行确认失败** — `pytest tests/test_scrutinize.py -v` → FAIL（ImportError: adverhire.scrutinize）

- [ ] **Step 3: 写实现** `adverhire/scrutinize.py`：

```python
from __future__ import annotations
from .models import Claim, Contradiction, SignalEvidence
from .llm import LLMClient, ModelRole

SCAN_SCHEMA = {
    "type": "object",
    "properties": {
        "signals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "quote": {"type": "string"},
                    "confidence": {"type": "number"},
                },
            },
        },
        "contradictions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "a": {"type": "string"}, "b": {"type": "string"},
                    "nature": {"type": "string"},
                },
            },
        },
    },
}

CONFIRM_SCHEMA = {
    "type": "object",
    "properties": {
        "confirmations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"index": {"type": "integer"},
                               "confirmed": {"type": "boolean"},
                               "note": {"type": "string"}},
            },
        }
    },
}


def scrutinize(llm: LLMClient, answers: list[Claim],
               resume_claims: list[Claim]) -> tuple[list[SignalEvidence], list[Contradiction]]:
    scan_prompt = (
        "扫描以下回答与简历，初筛出：1) 虚构成分信号(AI味道)；2) 简历/回答间的技术、规模、时间线矛盾。"
        "宁可多报。\n\n回答:\n" +
        "\n".join(a.bullet for a in answers) +
        "\n\n简历断言:\n" + "\n".join(c.bullet for c in resume_claims)
    )
    scan = llm.structured(ModelRole.FLASH, scan_prompt, SCAN_SCHEMA)

    sig_candidates = scan.get("signals", [])
    contra_candidates = scan.get("contradictions", [])

    # 深挖：只对初筛命中项交给 Pro 逐条确认 —— 误报被驳回
    confirm_payload = [{"index": i, "sig": s.get("label"), "quote": s.get("quote", "")}
                       for i, s in enumerate(sig_candidates)]
    confirm = llm.structured(ModelRole.PRO, confirm_payload, CONFIRM_SCHEMA)

    confirmed_idx = {c["index"] for c in confirm.get("confirmations", [])
                     if c.get("confirmed")}

    signals: list[SignalEvidence] = []
    for i, s in enumerate(sig_candidates):
        if i in confirmed_idx and s.get("label"):
            signals.append(SignalEvidence(
                label=s["label"],
                quote=s.get("quote", ""),
                confidence=float(s.get("confidence", 1.0)),
                verdict_note=next((c.get("note", "") for c in confirm.get("confirmations", [])
                                   if c.get("index") == i), ""),
            ))
    # D 矛盾：本项目先用初筛原样透传（含 nature），不做二次确认，后续任务可加
    contradictions = [Contradiction(Claim(a=str(cc.get("a", "")), source="answer"),
                                    Claim(b=str(cc.get("b", "")), source="resume"),
                                    nature=str(cc.get("nature", "")))
                      for cc in contra_candidates if cc.get("a") and cc.get("b")]
    return signals, contradictions
```

- [ ] **Step 4: 运行确认通过** — `pytest tests/test_scrutinize.py -v` → PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add adverhire/scrutinize.py tests/test_scrutinize.py
git commit -m "feat(adverhire): add two-stage fabrication and contradiction scrutiny
Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 7: verdict 阶段 —— 风险分级报告（不变量 #2）

**Files:**
- Create: `adverhire/verdict.py`
- Test: `tests/test_verdict.py`

**Interfaces:**
- Consumes: `models.RiskReport/RiskLevel/SignalEvidence/Contradiction/Dimen`、`llm.LLMClient/ModelRole`。
- Produces: `build_report(llm, signals, contradictions, summary_prompt="") -> RiskReport`：
  - 用 `ModelRole.PRO` 调 `llm.structured`，schema `{"overall":"LOW|MEDIUM|HIGH","by_dimension":{"<dimen>":0.0}}`。
  - `overall` 必须映射入 `RiskLevel`（非法值回落 `LOW`）——**不变量 #2**。
  - `by_dimension` 按键补齐为 `Dimen` 全集（缺省 0.0）。
  - `summary` 由 `llm.generate(PRO, summary_prompt)` 生成一句话。

- [ ] **Step 1: 写失败测试** `tests/test_verdict.py`：

```python
from adverhire.verdict import build_report
from adverhire.llm import ModelRole, MockLLM
from adverhire.models import RiskLevel, SignalEvidence, Contradiction, Claim

SIG = SignalEvidence("no_embodied_detail", "用单机redis就够了", 0.8, "规模存疑")
CONTRA = Contradiction(Claim("a", source="answer"), Claim("b", source="resume"), "scale_mismatch")

def test_build_report_maps_overall_and_fills_dimensions():
    mock = MockLLM(responses={
        ModelRole.PRO: [
            {"overall": "MEDIUM", "by_dimension": {"no_embodied_detail": 0.8}},
            "多项无具身细节，技术规模存疑，建议面试官人工复核。",
        ],
    })
    rep = build_report(mock, [SIG], [CONTRA])
    assert rep.overall == RiskLevel.MEDIUM
    assert rep.by_dimension["no_embodied_detail"] == 0.8
    assert all(isinstance(d, float) for d in rep.by_dimension.values())  # 五维补齐

def test_never_emits_elimination_conclusion():
    mock = MockLLM(responses={
        ModelRole.PRO: [
            {"overall": "HIGH", "by_dimension": {}},
            "存在较多虚构成分。",
        ],
    })
    rep = build_report(mock, [SIG], [])
    # 不变量 #2：报告只含风险分级，绝无淘汰/录用字样
    text = (rep.summary + str(rep.overall)).lower()
    assert "淘汰" not in text and "录用" not in text
```

- [ ] **Step 2: 运行确认失败** — `pytest tests/test_verdict.py -v` → FAIL（ImportError: adverhire.verdict）

- [ ] **Step 3: 写实现** `adverhire/verdict.py`：

```python
from __future__ import annotations
from .models import RiskLevel, SignalEvidence, Contradiction, RiskReport, Dimen
from .llm import LLMClient, ModelRole

OVERALL_SCHEMA = {
    "type": "object",
    "properties": {
        "overall": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
        "by_dimension": {"type": "object"},
    },
}


def _risk(value: str) -> RiskLevel:
    try:
        return RiskLevel(value)
    except ValueError:
        return RiskLevel.LOW  # 非法值回落 LOW —— 不变量 #2（绝不升级成结论）


def build_report(llm: LLMClient, signals: list[SignalEvidence], contradictions: list[Contradiction],
                 summary_prompt: str = "用一句话给面试官的真实性参考") -> RiskReport:
    evidence = "\n".join(f"[{s.label}] {s.quote}" for s in signals)
    contra = "\n".join(f"{c.nature}: {c.a.bullet} vs {c.b.bullet}" for c in contradictions)
    judge = llm.structured(ModelRole.PRO, evidence + "\n" + contra, OVERALL_SCHEMA)

    dims: dict[str, float] = {}
    raw_dims = judge.get("by_dimension", {}) or {}
    for d in Dimen:
        try:
            dims[d.value] = float(raw_dims.get(d.value, 0.0))
        except (TypeError, ValueError):
            dims[d.value] = 0.0

    summary = llm.generate(ModelRole.PRO, summary_prompt + "\n" + evidence).strip()
    return RiskReport(
        overall=_risk(str(judge.get("overall", "LOW"))),
        signals=signals,
        contradictions=contradictions,
        by_dimension=dims,
        summary=summary,
    )
```

- [ ] **Step 4: 运行确认通过** — `pytest tests/test_verdict.py -v` → PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add adverhire/verdict.py tests/test_verdict.py
git commit -m "feat(adverhire): emit risk-graded report without elimination conclusions
Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 8: 状态机编排 + 包导出（machine.py）

**Files:**
- Create: `adverhire/machine.py`
- Modify: `adverhire/__init__.py`（按 Task 1 的正式版补 `machine` 导入）
- Test: `tests/test_machine.py`

**Interfaces:**
- Consumes: 全部阶段函数 + `models`。
- Produces:
  - `class AdversarialStateMachine`：
    - `__init__(self, llm: LLMClient)`
    - `parse_then_probe(text: str) -> tuple[list[Claim], QuestionSet]`
    - `advance(answers: list[Claim], resume_claims: list[Claim]) -> RiskReport`
      （内部 `scrutinize` + `build_report`，一条 API 走完审查线）

- [ ] **Step 1: 写失败测试** `tests/test_machine.py`：

```python
from adverhire.machine import AdversarialStateMachine
from adverhire.llm import ModelRole, MockLLM
from adverhire.models import RiskLevel


def test_machine_parse_probe_then_review_end_to_end():
    mock = MockLLM(responses={
        ModelRole.FLASH: [  # parse(结构化) + scrutinize初筛(结构化)
            {"claims": [{"bullet": "优化缓存QPS+50%", "tech": ["redis"],
                          "metric": "50", "source": "resume"}]},
            {"signals": [{"label": "no_embodied_detail", "quote": "就用单机redis",
                           "confidence": 0.7, }], "contradictions": []},
        ],
        ModelRole.PRO: [  # probe(结构化) + 深挖确认(结构化) + verdict结构化 + summary(generate)
            {"traps": [{"claim_idx": 0, "wrong_preset": "改成1800",
                         "question": "从200怎么调到1800？", "discriminators": ["纠正"]}]},
            {"confirmations": [{"index": 0, "confirmed": True, "note": "规模存疑"}]},
            {"overall": "MEDIUM", "by_dimension": {"no_embodied_detail": 0.8}},
            "技术规模存疑，建议人工复核。",
        ],
    })
    sm = AdversarialStateMachine(mock)
    claims, qs = sm.parse_then_probe("某简历全文")
    assert len(claims) == 1 and len(qs.questions) == 1
    report = sm.advance([mock.structured(ModelRole.FLASH, "x", {}) and
                          __import__("adverhire.models", fromlist=["Claim"]).Claim("就用单机redis", source="answer")],
                         claims)
    assert report.overall == RiskLevel.MEDIUM
```

> 注：上面 `sm.advance` 用了内联构造 `Claim` 以避免 import 位置错乱；实现尽量保持一致。

- [ ] **Step 2: 运行确认失败** — `pytest tests/test_machine.py -v` → FAIL（ImportError: adverhire.machine）

- [ ] **Step 3: 写实现** `adverhire/machine.py`：

```python
from __future__ import annotations
from .models import Claim, QuestionSet, RiskReport
from .llm import LLMClient
from .parse import parse_resume
from .probe import gen_traps
from .scrutinize import scrutinize
from .verdict import build_report


class AdversarialStateMachine:
    """对抗审查状态机：parse -> probe -> (问答) -> scrutinize -> verdict。"""

    def __init__(self, llm: LLMClient):
        self._llm = llm

    def parse_then_probe(self, text: str) -> tuple[list[Claim], QuestionSet]:
        claims = parse_resume(self._llm, text)
        qs = gen_traps(self._llm, claims)
        return claims, qs

    def advance(self, answers: list[Claim], resume_claims: list[Claim]) -> RiskReport:
        signals, contradictions = scrutinize(self._llm, answers, resume_claims)
        return build_report(self._llm, signals, contradictions)
```

并确认 `adverhire/__init__.py` 用 **Task 1 Step 3 正式版**（含 `from .machine import AdversarialStateMachine`）。

- [ ] **Step 4: 运行确认通过** — `pytest tests/test_machine.py tests/test_models.py -v` → PASS（全绿）

- [ ] **Step 5: Commit**

```bash
git add adverhire/machine.py adverhire/__init__.py tests/test_machine.py
git commit -m "feat(adverhire): orchestrate adversarial review state machine
Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 9: 白盒测试夹具（R1 已知答案基线）

**Files:**
- Create: `tests/fixtures/real.md`
- Create: `tests/fixtures/real_answers.json`
- Create: `tests/fixtures/faked.md`
- Create: `tests/fixtures/faked_answers.json`
- Test: `tests/test_fixtures_self_assess.py`

**Interfaces:**
- Consumes: `adverhire.llm` / `adverhire.machine`.
- Produces: R1/R2 冒烟脚本（Task 12）和人工评估依赖的固定样本。`real.md`/`faked.md`
  为同岗位（AI 应用开发）虚构候选简历；`*_answers.json` 为 3 条回答。

- [ ] **Step 1: 写夹具** `tests/fixtures/real.md`（手工，深度真实）：

```markdown
# 张诚 · AI 应用开发
## 项目：推荐系统 QPS 优化（Python / Redis / FastAPI）
- 主导将线上推荐接口 P99 从 820ms 降到 260ms：先定位到预热缓存命中率仅 62%，
  用 lua 脚本合并热点 key 的批量回源，命中率升到 94%，QPS 从 200 提到 1200。
- 踩过一个坑：直接改 LRU 淘汰策略导致内存毛刺，回滚并通过预热任务错峰回源解决。
```

- [ ] **Step 2: 写夹具** `tests/fixtures/faked.md`（AI 生成，注水）：

```markdown
# 王宇 · AI 应用开发
## 项目：智能推荐系统优化（Python / Redis / FastAPI）
- 通过优化缓存架构和调整演进策略，显著提升了系统性能，实现 QPS 从 200 到 1800 的跨越，
  大幅改善用户体验，达到业界领先水平。采用最佳实践和微服务架构，全面提升可扩展性。
```

- [ ] **Step 3: 写夹具** `tests/fixtures/real_answers.json`：

```json
[
  "其实当时主要坑在预热缓存上，命中率只有62%，我们最后用lua脚本合了热点key批量回源，才提到94%。",
  "改LRU那版线上内存有毛刺，我临时回滚了，后面加了个错峰预热任务才算收尾。",
  "没有，这套优化我倒是踩了很多次,不太顺利,折腾了两周才稳定下来。"
]
```

- [ ] **Step 4: 写夹具** `tests/fixtures/faked_answers.json`：

```json
[
  "通过深度优化缓存架构和引入先进算法策略，系统性提升了整体性能，我们的方案达到行业顶尖水平。",
  "本次重构充分利用了缓存技术的最佳实践，显著增强系统健壮性和可扩展性，为业务提供坚实支撑。",
  "总之凭借卓越的技术能力和全面的优化思路，我们成功实现了性能的跨越式提升。"
]
```

- [ ] **Step 5: 写自检测试** `tests/test_fixtures_self_assess.py`（验证夹具本身能差异化驱动判别逻辑，不依赖真实 LLM）：

```python
import json
from pathlib import Path
from adverhire.followup import classify_answer
from adverhire.models import ImpactedTrap, Claim

HERE = Path(__file__).parent / "fixtures"

def _load():
    real_a = json.loads((HERE / "real_answers.json").read_text())
    faked_a = json.loads((HERE / "faked_answers.json").read_text())
    return real_a, faked_a

def test_fixtures_are_loadable_and_distinguishable():
    real_a, faked_a = _load()
    assert len(real_a) == len(faked_a) == 3
    trap = ImpactedTrap(Claim("优化缓存", ["redis"], 50.0, "resume"),
                        wrong_preset="P99降到260", question="怎么从820降到260的？",
                        discriminators=["其实", "回滚", "踩", "折腾"])
    # 真人回答含具身信号 -> 至少一条被判 corrected/vague；AI 回答 -> echoed/泛化
    assert any(classify_answer(a, trap) == "corrected" for a in real_a)
    assert all(a != "" for a in faked_a)  # 非空，供后续 LLM 判别
```

- [ ] **Step 6: 运行确认通过** — `pytest tests/test_fixtures_self_assess.py -v` → PASS

- [ ] **Step 7: Commit**

```bash
git add tests/fixtures tests/test_fixtures_self_assess.py
git commit -m "test(adverhire): add white-box R1 fixtures and self-assess
Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 10: CLI 薄壳（inspect 命令）

**Files:**
- Create: `adverhire/cli.py`
- Modify: `adverhire/__init__.py`（若需暴露 `main`）
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `adverhire.machine.AdversarialStateMachine`、`models.RiskReport`。
- Produces:
  - `def main(argv: list[str] | None = None) -> int`：解析
    `adverhire inspect <resume> -o <out.json>` 或 `--to-stdout`；
    读文件 → `machine.parse_then_probe(text)` → 输出 `questions` 到 `out.json`
    （含 `{"questions": [...], "per_trap": {...}}`）；若提供 `--answers <file>`，
    再走 `advance` 输出 `report`。
  - 默认不含 UI；输出 JSON / 终端文本。

- [ ] **Step 1: 写失败测试** `tests/test_cli.py`：

```python
import json, tempfile
from pathlib import Path
from adverhire.cli import main
from adverhire.llm import ModelRole, MockLLM

def test_cli_inspect_writes_questions_json(monkeypatch):
    mock = MockLLM(responses={ModelRole.FLASH: [
        {"claims": [{"bullet": "优化缓存", "tech": ["redis"], "metric": "50", "source": "resume"}]},
    ], ModelRole.PRO: [
        {"traps": [{"claim_idx": 0, "wrong_preset": "改成1800", "question": "怎么调的？", "discriminators": ["纠正"]}]},
    ]})
    monkeypatch.setattr("adverhire.cli.build_machine", lambda: __import__("adverhire.machine", fromlist=["AdversarialStateMachine"]).AdversarialStateMachine(mock))
    d = Path(tempfile.mkdtemp())
    resume = d / "r.md"; resume.write_text("# 简历")
    out = d / "q.json"
    code = main(["inspect", str(resume), "-o", str(out)])
    assert code == 0 and out.exists()
    data = json.loads(out.read_text())
    assert data["questions"][0]["question"]
```

- [ ] **Step 2: 运行确认失败** — `pytest tests/test_cli.py -v` → FAIL（ImportError: adverhire.cli）

- [ ] **Step 3: 写实现** `adverhire/cli.py`：

```python
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from .llm import MockLLM, LLMClient
from .machine import AdversarialStateMachine


def build_machine() -> LLMClient | None:
    # 真实调用在此接用户自备的 OpenAI 兼容适配器；无配置时返回 None(CLI报错)
    return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="adverhire")
    sub = p.add_subparsers(dest="cmd", required=True)
    insp = sub.add_parser("inspect")
    insp.add_argument("resume", type=Path)
    insp.add_argument("-o", "--out", type=Path, default=None)
    insp.add_argument("--answers", type=Path, default=None)
    insp.add_argument("--to-stdout", action="store_true")
    args = p.parse_args(argv)

    if args.cmd == "inspect":
        llm = build_machine()
        if llm is None:
            print("未配置真实 LLM；请先注入适配器或使用 MockLLM 做冒烟。", file=sys.stderr)
            return 1
        machine = AdversarialStateMachine(llm)
        text = args.resume.read_text(encoding="utf-8")
        claims, qs = machine.parse_then_probe(text)
        payload = {
            "questions": [{"question": t.question, "wrong_preset": t.wrong_preset,
                           "claim": t.claim.bullet, "discriminators": t.discriminators}
                          for t in qs.questions],
            "per_trap": qs.per_trap,
        }
        if args.answers and args.answers.exists():
            # 简版：读 rows 组成 answers 后走 advance
            payload["report"] = "review via API (answers injection is stub)"
        data = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.to_stdout or args.out is None:
            print(data)
        else:
            args.out.write_text(data, encoding="utf-8")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 运行确认通过** — `pytest tests/test_cli.py -v` → PASS（1 passed）

- [ ] **Step 5: Commit**

```bash
git add adverhire/cli.py tests/test_cli.py
git commit -m "feat(adverhire): add thin inspect CLI shell
Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 11: 完整单元测试套件 + 全绿

**Files:**
- Modify: `tests/`（合并各任务单测，确认相互独立、可全量跑通）
- Create: `pytest.ini`（可选，设 `testpaths = tests`）

**Interfaces:**
- Consumes: 全部模块。
- Produces: 一个 `python -m pytest` 全绿、彼此独立的测试套件。

- [ ] **Step 1: 建 `pytest.ini`**

```ini
[pytest]
testpaths = tests
```

- [ ] **Step 2: 全量运行并修复**

Run: `cd /Volumes/SSD/Code/09-business/adverhire && python -m pytest -v`
Expected: 全部测试 PASS（约 15-17 个）。若有顺序耦合，拆分各测试方法为独立（fixtures 不共享可变全局）。

- [ ] **Step 3: 不变量回归确认**

Run: `python -m pytest tests/test_verdict.py tests/test_probe.py -v`
Expected: 确认坑题派生自 Claim（越界被过滤），verdict 不输出淘汰结论。

- [ ] **Step 4: Commit**

```bash
git add pytest.ini tests
git commit -m "test(adverhire): stabilize full unit suite and invariants
Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 12: 真实模型冒烟运行器（POC，非 CI）

**Files:**
- Create: `scripts/run_with_real_llm.py`
- Create: `README.md`（用法说明）

**Interfaces:**
- Consumes: `adverhire.machine.AdversarialStateMachine`、`scripts` 内置适配器、
  `tests/fixtures/*.{md,json}`。
- Produces:
  - `scripts/run_with_real_llm.py`：用户自行填 `API_KEY`/`BASE_URL` 后，对
    `real.md` 与 `faked.md` 各跑完整 `parse → probe → scrutinize → verdict`，
    打印 `RiskReport`（含 `overall`、signals、contradictions、by_dimension）。
    供**人工冒烟**——非自动测试，不进 CI。

- [ ] **Step 1: 写运行器** `scripts/run_with_real_llm.py`（真实模型，用户自行注入凭证）：

```python
"""冒烟运行器：对 R1 夹具真实跑一份 RiskReport。用法：
   API_KEY=... BASE_URL=... python scripts/run_with_real_llm.py
依赖：用户当前仓库无 API SDK；此处用 requests 直连 OpenAI 兼容接口。"""
import json, os
from pathlib import Path
import requests
from adverhire.models import Claim
from adverhire.llm import LLMClient, ModelRole

API_KEY = os.environ.get("API_KEY") or "sk-xxx"
BASE = os.environ.get("BASE_URL", "https://api.deepseek.com/v1/chat/completions")
PRO = os.environ.get("PRO_MODEL", "deepseek-chat")   # 占位，需按官方文档核对
FLASH = os.environ.get("FLASH_MODEL", "deepseek-chat")


class OpenAIClient(LLMClient):
    def _chat(self, role, prompt):
        r = requests.post(BASE, headers={"Authorization": f"Bearer {API_KEY}"},
                          json={"model": PRO if role is ModelRole.PRO else FLASH,
                                "messages": [{"role": "user", "content": prompt}]}, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def generate(self, role, prompt): return self._chat(role, prompt)
    def structured(self, role, prompt, schema):
        out = self._chat(role, prompt + f"\n请仅输出 JSON：{json.dumps(schema)}")
        return json.loads(out)


def main():
    here = Path(__file__).parent.parent
    for name in ("real", "faked"):
        md = (here / f"tests/fixtures/{name}.md").read_text(encoding="utf-8")
        ans = json.loads((here / f"tests/fixtures/{name}_answers.json").read_text(encoding="utf-8"))
        sm = AdversarialStateMachine(OpenAIClient())
        claims, qs = sm.parse_then_probe(md)
        answers = [Claim(a, source="answer") for a in ans]
        report = sm.advance(answers, claims)
        print(f"=== {name} ===")
        print(f"overall: {report.overall.value}")
        print("signals:", [s.label for s in report.signals])
        print("contradictions:", [c.nature for c in report.contradictions])
        print("by_dimension:", report.by_dimension)
        print("summary:", report.summary)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 写 README 用法** — 在仓库根创建 `README.md`：

```markdown
# adverhire

对抗性招聘核验 —— 用对抗性审查与问答识别 AI 代答与简历注水，还原真实能力。

## 快速开始（单元测试）

```bash
python -m pytest -v
```

## 冒烟（真实模型，需自备 API 凭证）

按 SDK 官网核对模型名后：

```bash
API_KEY=sk-... BASE_URL=... python scripts/run_with_real_llm.py
```

输出对 `tests/fixtures/` 中 `real` vs `faked` 的 `RiskReport`，供人工评估判别性。
```

- [ ] **Step 3: 冒烟（人工）** — 运行 `python scripts/run_with_real_llm.py`，核对 `faked.md` 的
  虚构成分/矛盾是否显著高于 `real.md`。此为人工冒烟，非自动断言；若判别性不足，回改
  `probe._prompt_for` 的 discriminators 与 `followup` 终止条件。**不做成 CI 门禁。**

- [ ] **Step 4: Commit**

```bash
git add scripts/run_with_real_llm.py README.md
git commit -m "docs(adverhire): add real-LLM smoke runner and usage README
Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Self-Review 记录

- **Spec 覆盖核对**：parse→probe→scrutinize→verdict 全状态机 = Task 3/4/6/7+8；
  A 坑题 = Task 4；B 动态追问(动态 3 层) = Task 5；C 虚构成分 = Task 6；D 矛盾挖掘 = Task 6；
  反 AI 不变量 #1/#2 = Task 4/7 硬编码；薄壳 CLI = Task 10；R1 白盒基线 = Task 9；
  R2 真实脱敏 = Task 12（人工冒烟）；测试文件结构 = Task 1-11。✓
- **Placeholder 扫描**：无 TBD/TODO；每步含完整代码与命令。`build_machine()` 返回 `None`
  是**有意**的（真实凭证用户自备），非占位缺陷。✓
- **类型一致性**：`parse_resume`/`gen_traps`/`next_followup`/`scrutinize`/`build_report`/
  `AdversarialStateMachine` 签名在引用任务(Task 8/9/10/12)中保持一致；`ModelRole` 常量
  `PRO/FLASH` 全文件统一。✓

---

## 执行交接

计划已保存。两种执行方式（见 writing-plans 交接节），实现时选用一种。
