from __future__ import annotations

import pytest

from harnessable import CodeExecutionContract, CodeExecutionHarness, HarnessKernel, code_execution_capability
from harnessable.decisions import DecisionEffect
from harnessable.events import EventType, HarnessEvent
from harnessable.gateways import GatewayContext, ToolCallRequest, ToolGateway
from harnessable.resilience import FallbackManager, FallbackPolicyRegistry, FallbackPolicy
from harnessable.resilience.failure_signal import FailureCategory, FailureLayer, FailureSignal


def safe_contract() -> CodeExecutionContract:
    return CodeExecutionContract(
        backend="docker",
        filesystem={
            "readwrite": "temporary_workspace_copy",
            "readwrite_paths": ["D:/tmp/harnessdiff-code/workspace"],
            "workspace_writeback": "none",
        },
        network={"default_policy": "block"},
        resources={"timeout_seconds": 120, "memory": "1g", "cpus": 1, "pids": 256},
        trust_level="stable",
    )


@pytest.mark.asyncio
async def test_code_execution_harness_allows_constrained_runtime():
    kernel = HarnessKernel()
    CodeExecutionHarness.install(kernel)
    capability = code_execution_capability(
        capability_id="tool.code.docker",
        backend="docker",
        filesystem=safe_contract().filesystem,
        network=safe_contract().network,
        resources=safe_contract().resources,
        trust_level="stable",
    )
    gateway = ToolGateway(kernel, {"run": lambda command: command}, capability=capability)

    result = await gateway.call(
        ToolCallRequest("run", {"command": "python --version"}),
        GatewayContext(run_id="run_code", runtime_type="agent"),
    )

    assert result.ok is True
    assert result.command.command_type.value == "CONTINUE"


@pytest.mark.asyncio
async def test_code_execution_harness_blocks_secret_and_broad_write():
    kernel = HarnessKernel()
    CodeExecutionHarness.install(kernel)
    capability = code_execution_capability(
        capability_id="tool.code.unsafe",
        backend="mxc",
        filesystem={"readwrite_paths": ["C:/"], "readonly_paths": ["C:/repo/.env"]},
        network={"default_policy": "block"},
        resources={"timeout_seconds": 120, "memory": "1g", "cpus": 1, "pids": 256},
    )
    gateway = ToolGateway(kernel, {"run": lambda command: command}, capability=capability)

    result = await gateway.call(
        ToolCallRequest("run", {"command": "python --version"}),
        GatewayContext(run_id="run_code", runtime_type="agent"),
    )

    assert result.ok is False
    assert result.command.command_type.value == "BLOCK"


def test_code_execution_harness_requires_approval_for_network_or_missing_limits():
    kernel = HarnessKernel()
    CodeExecutionHarness.install(kernel)
    capability = code_execution_capability(
        capability_id="tool.code.needs_approval",
        backend="mxc",
        filesystem=safe_contract().filesystem,
        network={"default_policy": "allow"},
        resources={"timeout_seconds": 120},
    )
    decision = kernel.emit(
        HarnessEvent(
            event_id="evt_code",
            run_id="run_code",
            event_type=EventType.TOOL_CALL_REQUESTED,
            runtime_type="agent",
            capability=capability.to_dict(),
            payload={"request": ToolCallRequest("run", {"command": "node --version"})},
        )
    )

    assert decision.effect == DecisionEffect.REQUIRE_APPROVAL
    assert "CODE_EXECUTION_NETWORK_OPEN" in str(decision.reason)


def test_code_execution_harness_warns_for_preview_enforcement_gaps():
    kernel = HarnessKernel()
    CodeExecutionHarness.install(kernel)
    capability = code_execution_capability(
        capability_id="tool.code.mxc_preview",
        backend="mxc",
        filesystem=safe_contract().filesystem,
        network=safe_contract().network,
        resources=safe_contract().resources,
        trust_level="preview",
        enforcement_gaps=["mxc_preview_not_security_boundary"],
    )
    decision = kernel.emit(
        HarnessEvent(
            event_id="evt_code",
            run_id="run_code",
            event_type=EventType.TOOL_CALL_REQUESTED,
            runtime_type="agent",
            capability=capability.to_dict(),
            payload={"request": ToolCallRequest("run", {"command": "python --version"})},
        )
    )

    assert decision.effect == DecisionEffect.WARN
    assert "CODE_EXECUTION_ENFORCEMENT_GAPS" in str(decision.reason)


def test_code_execution_fallback_cannot_widen_permission_boundary():
    registry = FallbackPolicyRegistry()
    registry.add(
        FallbackPolicy(
            id="code_exec_fallback",
            name="Code execution fallback",
            constraints={"max_total_attempts": 1, "never_degrade": ["tool_permission"]},
            applies_to={"event_types": ["TOOL_CALL_FAILED"], "capability_types": ["TOOL"]},
            fallback_graph=[
                {
                    "id": "fallback_to_wider_runtime",
                    "action": {
                        "type": "ROUTE",
                        "selector": {
                            "permission_boundary": "wider",
                            "same_or_stricter_data_policy": True,
                            "same_or_stricter_permission_boundary": False,
                        },
                    },
                }
            ],
        )
    )
    event = HarnessEvent(
        event_id="evt_failed",
        run_id="run_code",
        event_type=EventType.TOOL_CALL_FAILED,
        capability={"type": "TOOL"},
    )

    plan = FallbackManager(registry).plan(
        event,
        FailureSignal(
            run_id="run_code",
            event_id="evt_failed",
            layer=FailureLayer.TOOL,
            category=FailureCategory.TIMEOUT,
            evidence={"message": "MXC unavailable"},
        ),
    )

    assert plan.decision.effect == DecisionEffect.BLOCK
    assert plan.blocked_reason == "unsafe fallback target"
