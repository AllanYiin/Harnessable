import pytest

from harnessable import HarnessKernel
from harnessable.gateways import GatewayContext, ModelChunk, ModelGateway, ModelRequest


@pytest.mark.asyncio
async def test_model_gateway_stream_provider_preserves_usage_metadata():
    async def provider(request, context):
        yield ModelChunk("hello ")
        yield ModelChunk("world", usage={"input_tokens": 1, "output_tokens": 2, "total_tokens": 3})

    kernel = HarnessKernel()
    gateway = ModelGateway(kernel, stream_provider=provider)

    chunks = [chunk async for chunk in gateway.call_stream(ModelRequest("hello"), GatewayContext(run_id="run_usage"))]

    assert "".join(chunk.text for chunk in chunks) == "hello world"
    assert chunks[-1].usage["total_tokens"] == 3
    completed = [record.payload for record in kernel.traces.by_kind("event") if record.payload["event_type"] == "MODEL_CALL_COMPLETED"]
    assert completed[-1]["metadata"]["usage"]["total_tokens"] == 3
