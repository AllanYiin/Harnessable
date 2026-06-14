import pytest

from harnessable.adapters import ChatRuntimeAdapter
from harnessable.decisions import DecisionEffect, ExecutionGovernor, HarnessDecision, RuntimeCommandType
from harnessable.gateways import ModelChunk


class FixedDecisionKernel:
    def __init__(self, decision: HarnessDecision) -> None:
        self.decision = decision
        self.governor = ExecutionGovernor()

    def emit(self, event):
        self.event = event
        return self.decision


class RecordingModelGateway:
    def __init__(self) -> None:
        self.calls = []

    async def call_stream(self, request, context):
        self.calls.append((request, context))
        yield ModelChunk(f"model:{request.prompt}")


async def _run_chat(decision: HarnessDecision, text: str = "original"):
    gateway = RecordingModelGateway()
    kernel = FixedDecisionKernel(decision)
    chunks = [chunk async for chunk in ChatRuntimeAdapter(kernel, gateway).run_stream(text, {"run_id": "run_dispatch"})]
    return chunks, gateway


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("effect", "command_type"),
    [
        (DecisionEffect.BLOCK, RuntimeCommandType.BLOCK),
        (DecisionEffect.ABORT, RuntimeCommandType.ABORT),
        (DecisionEffect.FAIL_SAFE, RuntimeCommandType.FAIL_SAFE),
        (DecisionEffect.REQUIRE_APPROVAL, RuntimeCommandType.REQUEST_APPROVAL),
        (DecisionEffect.ROLLBACK, RuntimeCommandType.ROLLBACK),
    ],
)
async def test_terminal_chat_commands_stop_before_model_call(effect, command_type):
    chunks, gateway = await _run_chat(HarnessDecision(event_id="evt", effect=effect))

    assert [chunk.text for chunk in chunks] == [""]
    assert chunks[0].command.command_type == command_type
    assert chunks[0].metadata == {"stopped": True}
    assert gateway.calls == []


@pytest.mark.asyncio
async def test_continue_chat_command_streams_original_prompt():
    chunks, gateway = await _run_chat(HarnessDecision(event_id="evt", effect=DecisionEffect.ALLOW))

    assert [chunk.text for chunk in chunks] == ["model:original"]
    assert chunks[0].command.command_type == RuntimeCommandType.CONTINUE
    assert chunks[0].metadata["runtime_command"] == "CONTINUE"
    assert gateway.calls[0][0].prompt == "original"


@pytest.mark.asyncio
async def test_mutate_chat_command_streams_mutated_prompt():
    decision = HarnessDecision(
        event_id="evt",
        effect=DecisionEffect.TRANSFORM,
        mutation={"value": "mutated"},
    )

    chunks, gateway = await _run_chat(decision)

    assert [chunk.text for chunk in chunks] == ["model:mutated"]
    assert chunks[0].command.command_type == RuntimeCommandType.MUTATE
    assert chunks[0].metadata["mutation"] == {"value": "mutated"}
    assert gateway.calls[0][0].prompt == "mutated"


@pytest.mark.asyncio
async def test_retry_chat_command_preserves_retry_metadata_and_prompt_override():
    decision = HarnessDecision(
        event_id="evt",
        effect=DecisionEffect.RETRY,
        retry={"prompt": "retry prompt", "attempt": 2},
    )

    chunks, gateway = await _run_chat(decision)

    assert [chunk.text for chunk in chunks] == ["model:retry prompt"]
    assert chunks[0].command.command_type == RuntimeCommandType.RETRY
    assert chunks[0].metadata["retry"] == {"prompt": "retry prompt", "attempt": 2}
    assert gateway.calls[0][1].metadata["retry"]["attempt"] == 2


@pytest.mark.asyncio
async def test_route_chat_command_preserves_route_metadata():
    decision = HarnessDecision(
        event_id="evt",
        effect=DecisionEffect.ROUTE,
        route={"target": "safer_model"},
    )

    chunks, gateway = await _run_chat(decision)

    assert [chunk.text for chunk in chunks] == ["model:original"]
    assert chunks[0].command.command_type == RuntimeCommandType.ROUTE
    assert chunks[0].metadata["route"] == {"target": "safer_model"}
    assert gateway.calls[0][1].metadata["route"]["target"] == "safer_model"
