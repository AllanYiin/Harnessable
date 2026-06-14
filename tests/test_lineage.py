from harnessable.lineage import LineageEnvelope, LineageStore
from harnessable.gateways import ModelChunk


def test_lineage_envelope_captures_provider_usage_and_source_refs():
    chunks = [
        ModelChunk("hello "),
        ModelChunk("world", usage={"input_tokens": 3, "output_tokens": 2, "total_tokens": 5}),
    ]

    envelope = LineageEnvelope.from_model_chunks(
        run_id="run_lineage",
        event_id="evt_model",
        chunks=chunks,
        prompt_version="prompt.v1",
        system_policy_version="policy.v1",
        dataset_refs=["dataset://golden"],
        source_refs=["source://doc#1"],
        claim_source_refs=["claim://answer/source://doc#1"],
        model_provider="provider.test",
        model_name="model.test",
        model_revision="rev1",
        cost={"usd": 0.001, "metering_source": "provider_usage"},
        latency_ms=12,
        adapter_metadata={"adapter": "test-double"},
    )
    restored = LineageEnvelope.from_dict(envelope.to_dict())

    assert restored.usage["total_tokens"] == 5
    assert restored.streaming is True
    assert restored.prompt_version == "prompt.v1"
    assert restored.source_refs == ["source://doc#1"]
    assert restored.cost["metering_source"] == "provider_usage"


def test_lineage_marks_missing_provider_usage_unknown():
    envelope = LineageEnvelope.from_model_chunks(run_id="run", event_id="evt", chunks=[ModelChunk("no usage")])

    assert envelope.to_dict()["usage"]["status"] == "unknown"
    assert envelope.to_dict()["usage"]["reason"] == "provider_usage_unavailable"


def test_lineage_store_returns_run_refs():
    store = LineageStore()
    envelope = store.add(LineageEnvelope(run_id="run", event_id="evt", envelope_id="lineage_fixed"))

    assert store.by_run("run") == [envelope]
    assert store.refs_for_run("run") == ["lineage://lineage_fixed"]

