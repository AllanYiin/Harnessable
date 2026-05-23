import asyncio

try:
    from _bootstrap import add_src_to_path
except ModuleNotFoundError:
    from examples._bootstrap import add_src_to_path

add_src_to_path()

from harnessable import HarnessKernel
from harnessable.adapters import ChatRuntimeAdapter


async def main() -> None:
    adapter = ChatRuntimeAdapter(HarnessKernel())
    async for chunk in adapter.run_stream("hello from chat", {"run_id": "run_chat"}):
        print(chunk.text, end="")


if __name__ == "__main__":
    asyncio.run(main())
