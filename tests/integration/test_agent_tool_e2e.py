import pytest

from harnessable import HarnessKernel
from harnessable.adapters import AgentRuntimeAdapter
from harnessable.gateways import ToolGateway


@pytest.mark.asyncio
async def test_agent_tool_gateway_e2e():
    kernel = HarnessKernel()
    adapter = AgentRuntimeAdapter(kernel, ToolGateway(kernel, {"echo": lambda text: text}))
    result = await adapter.call_tool("echo", {"text": "ok"}, {"run_id": "run_agent"})
    assert result.ok is True
    assert result.value.value == "ok"
    assert kernel.traces.by_kind("event")
