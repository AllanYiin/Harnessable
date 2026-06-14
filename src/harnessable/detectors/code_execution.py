from __future__ import annotations

from typing import Any

from harnessable.events import HarnessEvent

from .base import HarnessDetector
from .results import DetectionOutcome, DetectionResult


class CodeExecutionPolicyDetector(HarnessDetector):
    detector_id = "code_execution_policy_detector"

    def __init__(self, bucket: str | None = None) -> None:
        self.bucket = bucket

    def evaluate(
        self,
        event: HarnessEvent,
        state: object | None = None,
        artifacts: object | None = None,
    ) -> DetectionResult:
        contract = _code_execution_contract(event)
        if not contract:
            return DetectionResult(
                DetectionOutcome.CLEAN,
                reason={"code": "CODE_EXECUTION_CONTRACT_ABSENT"},
            )
        issues = _policy_issues(contract)
        if self.bucket:
            issues = [issue for issue in issues if issue.get("bucket") == self.bucket]
        if not issues:
            return DetectionResult(
                DetectionOutcome.CLEAN,
                reason={"code": "CODE_EXECUTION_POLICY_CLEAN", "bucket": self.bucket},
            )
        return DetectionResult(
            DetectionOutcome.DETECTED,
            reason={
                "code": "CODE_EXECUTION_POLICY_ISSUES",
                "bucket": self.bucket,
                "issues": issues,
                "issue_codes": [issue["code"] for issue in issues],
            },
        )


def _code_execution_contract(event: HarnessEvent) -> dict[str, Any]:
    capability_contract = (
        (event.capability or {}).get("contracts", {}).get("code_execution")
        if isinstance(event.capability, dict)
        else None
    )
    request = (event.payload or {}).get("request") if isinstance(event.payload, dict) else None
    request_args = getattr(request, "args", None)
    request_contract = None
    if isinstance(request_args, dict):
        request_contract = request_args.get("code_execution") or request_args.get("runtime_contract")
    if isinstance(request_contract, dict):
        merged = dict(capability_contract or {})
        merged.update(request_contract)
        return merged
    return dict(capability_contract or {})


def _policy_issues(contract: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    filesystem = contract.get("filesystem") or {}
    network = contract.get("network") or {}
    resources = contract.get("resources") or {}
    env = contract.get("env") or filesystem.get("env") or []

    if _network_is_open(network):
        issues.append(
            {
                "code": "CODE_EXECUTION_NETWORK_OPEN",
                "bucket": "approval",
                "message": "Code execution network policy is open or unspecified.",
            }
        )
    if _readwrite_scope_is_broad(filesystem):
        issues.append(
            {
                "code": "CODE_EXECUTION_READWRITE_SCOPE_BROAD",
                "bucket": "block",
                "message": "Code execution read-write paths are broader than a temporary workspace.",
            }
        )
    if _secret_env_exposed(env):
        issues.append(
            {
                "code": "CODE_EXECUTION_SECRET_ENV_EXPOSED",
                "bucket": "block",
                "message": "Code execution contract exposes secret-looking environment variables.",
            }
        )
    if _secret_path_exposed(filesystem):
        issues.append(
            {
                "code": "CODE_EXECUTION_SECRET_PATH_EXPOSED",
                "bucket": "block",
                "message": "Code execution filesystem policy exposes secret-bearing paths.",
            }
        )
    missing_limits = _missing_resource_limits(resources)
    if missing_limits:
        issues.append(
            {
                "code": "CODE_EXECUTION_RESOURCE_LIMITS_MISSING",
                "bucket": "approval",
                "message": "Code execution contract is missing resource limits.",
                "missing": missing_limits,
            }
        )
    gaps = list(contract.get("enforcement_gaps") or [])
    if gaps:
        issues.append(
            {
                "code": "CODE_EXECUTION_ENFORCEMENT_GAPS",
                "bucket": "warn",
                "message": "Code execution contract declares unsupported or preview enforcement gaps.",
                "gaps": gaps,
            }
        )
    if str(contract.get("trust_level") or "").lower() in {"preview", "experimental"}:
        issues.append(
            {
                "code": "CODE_EXECUTION_PREVIEW_TRUST_LEVEL",
                "bucket": "warn",
                "message": "Code execution backend is marked preview or experimental.",
            }
        )
    return issues


def _network_is_open(network: dict[str, Any]) -> bool:
    if not network:
        return True
    if network.get("allow_outbound") is True or network.get("allowOutbound") is True:
        return True
    policy = str(network.get("default_policy") or network.get("defaultPolicy") or "").lower()
    return policy not in {"block", "deny", "none", "disabled"}


def _readwrite_scope_is_broad(filesystem: dict[str, Any]) -> bool:
    paths = filesystem.get("readwrite_paths") or filesystem.get("readwritePaths") or []
    if filesystem.get("workspace_writeback") not in {None, False, "none"}:
        return True
    if filesystem.get("readwrite") == "temporary_workspace_copy":
        return False
    if not paths:
        return True
    for path in paths:
        normalized = str(path).replace("\\", "/").strip().lower()
        if normalized in {"", ".", "/", "*", "c:/", "c:", "/home", "/users"}:
            return True
        if normalized.endswith("/.ssh") or "/.ssh/" in normalized:
            return True
    return False


def _secret_env_exposed(env: Any) -> bool:
    items: list[str] = []
    if isinstance(env, dict):
        items = list(env.keys())
    elif isinstance(env, list):
        items = [str(item).split("=", 1)[0] for item in env]
    for key in items:
        upper = key.upper()
        if upper.endswith(("_KEY", "_TOKEN", "_SECRET")):
            return True
        if upper.startswith(("OPENAI_", "ANTHROPIC_", "AZURE_", "AWS_", "GOOGLE_", "GCP_", "SERPAPI_")):
            return True
    return False


def _secret_path_exposed(filesystem: dict[str, Any]) -> bool:
    paths = []
    paths.extend(filesystem.get("readonly_paths") or filesystem.get("readonlyPaths") or [])
    paths.extend(filesystem.get("readwrite_paths") or filesystem.get("readwritePaths") or [])
    for path in paths:
        normalized = str(path).replace("\\", "/").lower()
        if normalized.endswith("/.env") or "/.env." in normalized or "/.ssh" in normalized:
            return True
    return False


def _missing_resource_limits(resources: dict[str, Any]) -> list[str]:
    missing = []
    timeout = resources.get("timeout_seconds") or resources.get("timeoutMs") or resources.get("timeout_ms")
    if not timeout:
        missing.append("timeout")
    for key in ("memory", "cpus", "pids"):
        if key not in resources:
            missing.append(key)
    return missing
