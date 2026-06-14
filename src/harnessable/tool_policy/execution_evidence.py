from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CODE_EXECUTION_CAPABILITY_CLASS = "code_execution"
EXECUTION_EVIDENCE_POLICY_VERSION = 1

_EXECUTION_TERMS = (
    "run test",
    "run tests",
    "run pytest",
    "pytest",
    "unit test",
    "integration test",
    "e2e",
    "npm test",
    "npm run",
    "pnpm test",
    "pnpm run",
    "yarn test",
    "cargo test",
    "go test",
    "build",
    "compile",
    "execute",
    "執行",
    "跑測試",
    "執行測試",
    "測試",
    "建置",
    "編譯",
    "驗證",
)

_IMPLEMENTATION_TERMS = (
    "implement",
    "modify",
    "fix",
    "debug",
    "patch",
    "refactor",
    "write code",
    "add code",
    "update code",
    "修改",
    "實作",
    "修正",
    "除錯",
    "重構",
    "寫程式",
    "寫代碼",
    "加測試",
    "補測試",
    "請修改",
)

_CODE_CREATION_TERMS = (
    "create",
    "develop",
    "scaffold",
    "prototype",
    "新增",
    "建立",
    "撰寫",
    "開發",
    "製作",
    "打造",
    "建構",
)

_CODE_CONTEXT_TERMS = (
    "code",
    "repo",
    "repository",
    "runtime",
    "provider",
    "orchestrator",
    "api",
    "function",
    "class",
    "python",
    "typescript",
    "javascript",
    "node",
    "react",
    "vite",
    "pytest",
    "package.json",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    "程式",
    "代碼",
    "程式碼",
    "檔案",
    "測試",
    "錯誤",
    "報錯",
    "失敗",
    "後端",
    "前端",
)

_CODE_ARTIFACT_CONTEXT_TERMS = (
    "code",
    "app",
    "component",
    "frontend",
    "backend",
    "repo",
    "repository",
    "api",
    "function",
    "class",
    "python",
    "typescript",
    "javascript",
    "node",
    "react",
    "vite",
    "vitest",
    "pytest",
    "package.json",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    "程式",
    "代碼",
    "程式碼",
    "原型",
    "元件",
    "前端",
    "後端",
    "測試",
)

_EXPLANATION_STARTS = (
    "why ",
    "explain",
    "describe",
    "evaluate",
    "compare",
    "plan",
    "為何",
    "為什麼",
    "說明",
    "解釋",
    "評估",
    "比較",
    "規劃",
    "整理",
)

_EXPLANATION_ACTION_TERMS = (
    "please fix",
    "please implement",
    "please create",
    "please build",
    "fix ",
    "implement ",
    "請修改",
    "請修正",
    "請實作",
    "請建立",
    "請新增",
    "請開發",
    "請製作",
)

_PLANNING_ONLY_HINTS = (
    "重構方向",
    "重構建議",
    "refactor direction",
    "refactoring direction",
    "refactor plan",
)


@dataclass(slots=True)
class ExecutionEvidenceRequirement:
    requires_execution_evidence: bool = True
    required_capability_classes: list[str] = field(default_factory=lambda: [CODE_EXECUTION_CAPABILITY_CLASS])
    required_tool_names: list[str] = field(default_factory=list)
    reason: str = "coding_task_requires_executable_evidence"
    surface: str | None = None
    schema_version: int = EXECUTION_EVIDENCE_POLICY_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "requires_execution_evidence": self.requires_execution_evidence,
            "required_capability_classes": list(self.required_capability_classes),
            "required_tool_names": list(self.required_tool_names),
            "reason": self.reason,
        }
        if self.surface:
            payload["surface"] = self.surface
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionEvidenceRequirement":
        return cls(
            schema_version=int(data.get("schema_version") or EXECUTION_EVIDENCE_POLICY_VERSION),
            requires_execution_evidence=bool(data.get("requires_execution_evidence", True)),
            required_capability_classes=[str(item) for item in data.get("required_capability_classes") or [CODE_EXECUTION_CAPABILITY_CLASS]],
            required_tool_names=[str(item) for item in data.get("required_tool_names") or []],
            reason=str(data.get("reason") or "coding_task_requires_executable_evidence"),
            surface=data.get("surface"),
            metadata=dict(data.get("metadata") or {}),
        )


def build_execution_evidence_requirement(
    *,
    task_text: str,
    enabled: bool,
    code_execution_available: bool,
    required_tool_names: list[str] | tuple[str, ...] = (),
    surface: str | None = None,
) -> ExecutionEvidenceRequirement | None:
    if not enabled:
        return None
    if not code_execution_available:
        return None
    if not requires_code_execution_evidence(task_text):
        return None
    return ExecutionEvidenceRequirement(
        required_tool_names=[str(name) for name in required_tool_names],
        surface=surface,
    )


def requires_code_execution_evidence(task_text: str) -> bool:
    normalized = " ".join(task_text.lower().split())
    if not normalized:
        return False

    has_execution = _contains_any(normalized, _EXECUTION_TERMS)
    has_implementation = _contains_any(normalized, _IMPLEMENTATION_TERMS)
    has_code_context = _contains_any(normalized, _CODE_CONTEXT_TERMS)
    has_code_creation = _contains_any(normalized, _CODE_CREATION_TERMS)
    has_code_artifact_context = _contains_any(normalized, _CODE_ARTIFACT_CONTEXT_TERMS)
    has_code_creation_task = has_code_creation and has_code_artifact_context
    starts_as_explanation = normalized.startswith(_EXPLANATION_STARTS)
    has_explicit_action_after_explanation = _contains_any(normalized, _EXPLANATION_ACTION_TERMS)
    if starts_as_explanation and not has_explicit_action_after_explanation:
        return False
    if not has_execution and _contains_any(normalized, _PLANNING_ONLY_HINTS):
        return False
    if not has_execution and not has_implementation and not has_code_creation_task:
        return False
    if has_execution:
        return True
    if has_implementation and has_code_context:
        return True
    if has_code_creation_task:
        return True

    return has_implementation and not starts_as_explanation


def execution_policy_task_text(
    prompt: str,
    conversation_messages: tuple[dict[str, str], ...],
    *,
    max_messages: int = 6,
) -> str:
    parts: list[str] = []
    for message in conversation_messages[-max_messages:]:
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            parts.append(content.strip())
    if prompt.strip():
        parts.append(prompt.strip())
    return "\n".join(parts)


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)
