from harnessable import HarnessKernel
from harnessable.adapters import MultiAgentRuntimeAdapter


kernel = HarnessKernel()
adapter = MultiAgentRuntimeAdapter(kernel)
decision = adapter.handoff("reviewer", "please review", {"run_id": "run_multi"})
print(decision.effect.value)
