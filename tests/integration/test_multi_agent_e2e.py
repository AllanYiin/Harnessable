from harnessable import HarnessKernel
from harnessable.adapters import MultiAgentRuntimeAdapter


def test_multi_agent_handoff_e2e():
    decision = MultiAgentRuntimeAdapter(HarnessKernel()).handoff("reviewer", "review", {"run_id": "run_multi"})
    assert decision.effect.value == "ALLOW"
