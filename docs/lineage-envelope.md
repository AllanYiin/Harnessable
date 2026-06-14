# Lineage Envelope

Stage 18 adds `LineageEnvelope` for prompt, dataset, source, claim-source,
provider, usage, cost, latency, and streaming metadata.

The envelope is separate from rule decisions. It can be referenced from audit
packages through `lineage_refs`, and missing provider usage is recorded as
`unknown` instead of estimated as real usage.

## Model Stream Usage

`ModelChunk` now supports optional `usage` and `metadata` fields while keeping
the existing `.text` streaming contract.

Provider adapters may pass a `stream_provider` into `ModelGateway`. The gateway
still emits the normal `MODEL_CALL_REQUESTED` and `MODEL_CALL_COMPLETED` events.

## Example

```python
from harnessable.lineage import LineageEnvelope
from harnessable.gateways import ModelChunk

chunks = [ModelChunk("hello"), ModelChunk(" world", usage={"total_tokens": 2})]
envelope = LineageEnvelope.from_model_chunks(
    run_id="run_1",
    event_id="evt_model",
    chunks=chunks,
    model_provider="provider.test",
)
```

## Verification

```bash
python -m pytest tests/test_lineage.py tests/test_model_gateway_lineage.py tests/test_streaming_contract.py
```

