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
