import asyncio

try:
    from _bootstrap import add_src_to_path
except ModuleNotFoundError:
    from examples._bootstrap import add_src_to_path

add_src_to_path()

from harnessable import HarnessKernel
from harnessable.adapters import AgentRuntimeAdapter
from harnessable.gateways import ToolGateway


async def main() -> None:
    kernel = HarnessKernel()
    gateway = ToolGateway(kernel, {"echo": lambda text: text})
    adapter = AgentRuntimeAdapter(kernel, gateway)
    result = await adapter.call_tool("echo", {"text": "hello"}, {"run_id": "run_agent"})
    print(result.value.value)


if __name__ == "__main__":
    asyncio.run(main())
