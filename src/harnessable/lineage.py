from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class LineageEnvelope:
    run_id: str
    event_id: str
    envelope_id: str = field(default_factory=lambda: f"lineage_{uuid4().hex}")
    schema_version: str = "1"
    prompt_version: str | None = None
    system_policy_version: str | None = None
    dataset_refs: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    claim_source_refs: list[str] = field(default_factory=list)
    model_provider: str = "unknown"
    model_name: str = "unknown"
    model_revision: str = "unknown"
    usage: dict[str, Any] = field(default_factory=lambda: {"status": "unknown"})
    cost: dict[str, Any] = field(default_factory=lambda: {"status": "unknown"})
    latency_ms: int | None = None
    streaming: bool | str = "unknown"
    adapter_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "envelope_id": self.envelope_id,
            "run_id": self.run_id,
            "event_id": self.event_id,
            "prompt_version": self.prompt_version or "unknown",
            "system_policy_version": self.system_policy_version or "unknown",
            "dataset_refs": list(self.dataset_refs),
            "source_refs": list(self.source_refs),
            "claim_source_refs": list(self.claim_source_refs),
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "model_revision": self.model_revision,
            "usage": dict(self.usage),
            "cost": dict(self.cost),
            "latency_ms": self.latency_ms if self.latency_ms is not None else "unknown",
            "streaming": self.streaming,
            "adapter_metadata": dict(self.adapter_metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LineageEnvelope":
        payload = dict(data)
        if payload.get("prompt_version") == "unknown":
            payload["prompt_version"] = None
        if payload.get("system_policy_version") == "unknown":
            payload["system_policy_version"] = None
        if payload.get("latency_ms") == "unknown":
            payload["latency_ms"] = None
        return cls(**payload)

    @classmethod
    def from_model_chunks(
        cls,
        *,
        run_id: str,
        event_id: str,
        chunks: list[Any],
        prompt_version: str | None = None,
        system_policy_version: str | None = None,
        dataset_refs: list[str] | None = None,
        source_refs: list[str] | None = None,
        claim_source_refs: list[str] | None = None,
        model_provider: str = "unknown",
        model_name: str = "unknown",
        model_revision: str = "unknown",
        cost: dict[str, Any] | None = None,
        latency_ms: int | None = None,
        adapter_metadata: dict[str, Any] | None = None,
    ) -> "LineageEnvelope":
        usage = _last_usage(chunks)
        if not usage:
            usage = {"status": "unknown", "reason": "provider_usage_unavailable"}
        return cls(
            run_id=run_id,
            event_id=event_id,
            prompt_version=prompt_version,
            system_policy_version=system_policy_version,
            dataset_refs=dataset_refs or [],
            source_refs=source_refs or [],
            claim_source_refs=claim_source_refs or [],
            model_provider=model_provider,
            model_name=model_name,
            model_revision=model_revision,
            usage=usage,
            cost=cost or {"status": "unknown"},
            latency_ms=latency_ms,
            streaming=True,
            adapter_metadata=adapter_metadata or {},
        )


class LineageStore:
    def __init__(self) -> None:
        self.envelopes: dict[str, LineageEnvelope] = {}

    def add(self, envelope: LineageEnvelope) -> LineageEnvelope:
        self.envelopes[envelope.envelope_id] = envelope
        return envelope

    def by_run(self, run_id: str) -> list[LineageEnvelope]:
        return [envelope for envelope in self.envelopes.values() if envelope.run_id == run_id]

    def refs_for_run(self, run_id: str) -> list[str]:
        return [f"lineage://{envelope.envelope_id}" for envelope in self.by_run(run_id)]


def _last_usage(chunks: list[Any]) -> dict[str, Any]:
    usage: dict[str, Any] = {}
    for chunk in chunks:
        chunk_usage = getattr(chunk, "usage", None)
        if chunk_usage:
            usage = dict(chunk_usage)
    return usage

