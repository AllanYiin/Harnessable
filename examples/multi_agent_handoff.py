try:
    from _bootstrap import add_src_to_path
except ModuleNotFoundError:
    from examples._bootstrap import add_src_to_path

add_src_to_path()

from harnessable import HarnessKernel
from harnessable.adapters import MultiAgentRuntimeAdapter


kernel = HarnessKernel()
adapter = MultiAgentRuntimeAdapter(kernel)
decision = adapter.handoff("reviewer", "please review", {"run_id": "run_multi"})
print(decision.effect.value)
