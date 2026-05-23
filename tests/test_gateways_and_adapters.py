import pytest

from harnessable import HarnessKernel
from harnessable.decisions import DecisionEffect, RuntimeCommandType
from harnessable.events import EventType, HarnessEvent
from harnessable.gateways import ActionGateway, GatewayContext, ModelGateway, ModelRequest, ToolCallRequest, ToolGateway
from harnessable.capabilities import CapabilityHealth, HealthSnapshot
from harnessable.rules import HarnessRule
from harnessable.adapters import AgentRuntimeAdapter, ChatRuntimeAdapter, MultiAgentRuntimeAdapter


@pytest.mark.asyncio
async def test_gateway_block_does_not_execute_tool():
    kernel = HarnessKernel()
    kernel.register_rule(
        HarnessRule(
            id="block_tools",
            name="Block tools",
            applies_to={"event_types": ["TOOL_CALL_REQUESTED"], "capability_types": ["TOOL"]},
            detector={"type": "regex", "field": "payload.request.name", "pattern": "danger"},
            action={"when_detected": {"type": "BLOCK"}, "when_clean": {"type": "ALLOW"}},
        )
    )
    called = False

    def danger():
        nonlocal called
        called = True

    gateway = ToolGateway(kernel, {"danger": danger})
    result = await gateway.call(ToolCallRequest("danger"), GatewayContext(run_id="run_1"))
    assert result.ok is False
    assert result.command.command_type == RuntimeCommandType.BLOCK
    assert called is False


@pytest.mark.asyncio
async def test_model_gateway_streams():
    kernel = HarnessKernel()
    gateway = ModelGateway(kernel)
    chunks = [chunk.text async for chunk in gateway.call_stream(ModelRequest("hello world"), GatewayContext(run_id="run_1"))]
    assert "".join(chunks) == "hello world "


@pytest.mark.asyncio
async def test_gateway_respects_open_circuit_health():
    kernel = HarnessKernel()
    gateway = ToolGateway(kernel, {"ok": lambda: "ok"})
    kernel.health.set(gateway.capability.id, HealthSnapshot(status=CapabilityHealth.OPEN_CIRCUIT))
    result = await gateway.call(ToolCallRequest("ok"), GatewayContext(run_id="run_1"))
    assert result.ok is False
    assert "OPEN_CIRCUIT" in str(result.error)


@pytest.mark.asyncio
async def test_action_gateway_requires_idempotency_key():
    kernel = HarnessKernel()
    gateway = ActionGateway(kernel, {"send": lambda: "sent"})
    result = await gateway.call(ToolCallRequest("send"), GatewayContext(run_id="run_1"))
    assert result.ok is False
    assert "idempotency" in str(result.error)


@pytest.mark.asyncio
async def test_same_rule_across_chat_agent_multi_agent():
    kernel = HarnessKernel()
    kernel.register_rule(
        HarnessRule(
            id="universal_block",
            name="Universal block",
            applies_to={"runtimes": ["chat", "agent", "multi_agent"]},
            detector={"type": "always_allow"},
            action={"when_clean": {"type": "BLOCK"}},
        )
    )
    chat = ChatRuntimeAdapter(kernel)
    chat_chunks = [chunk.text async for chunk in chat.run_stream("hello", {"run_id": "run_chat"})]
    assert chat_chunks == [""]

    agent = AgentRuntimeAdapter(kernel)
    command = await agent.call_tool("noop", context={"run_id": "run_agent"})
    assert command.command_type == RuntimeCommandType.BLOCK

    multi = MultiAgentRuntimeAdapter(kernel)
    decision = multi.handoff("reviewer", context={"run_id": "run_multi"})
    assert decision.effect == DecisionEffect.BLOCK
