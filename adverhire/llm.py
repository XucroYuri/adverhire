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
