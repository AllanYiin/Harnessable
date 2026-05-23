import pytest

from harnessable import HarnessKernel
from harnessable.adapters import ChatRuntimeAdapter
from harnessable.rules import HarnessRule


@pytest.mark.asyncio
async def test_chat_e2e_rule_blocks_user_input():
    kernel = HarnessKernel()
    kernel.register_rule(
        HarnessRule(
            id="chat.block",
            name="Chat block",
            applies_to={"runtimes": ["chat"], "event_types": ["USER_INPUT_RECEIVED"]},
            detector={"type": "regex", "field": "payload.text", "pattern": "blocked"},
            action={"when_detected": {"type": "BLOCK"}, "when_clean": {"type": "ALLOW"}},
        )
    )
    chunks = [chunk.text async for chunk in ChatRuntimeAdapter(kernel).run_stream("blocked", {"run_id": "run_chat"})]
    assert chunks == [""]
    assert kernel.metrics.snapshot()["decision.BLOCK"] == 1
