import pytest

from harnessable import HarnessKernel
from harnessable.gateways import GatewayContext, ModelGateway, ModelRequest


@pytest.mark.asyncio
async def test_llm_output_streaming_contract():
    chunks = [chunk.text async for chunk in ModelGateway(HarnessKernel()).call_stream(ModelRequest("a b"), GatewayContext(run_id="run"))]
    assert chunks == ["a ", "b "]
