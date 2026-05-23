from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_VERSION = "1"

_OBJECT = {"type": "object"}

EVENT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["schema_version", "event_id", "run_id", "event_type"],
    "additionalProperties": False,
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "event_id": {"type": "string", "minLength": 1},
        "run_id": {"type": "string", "minLength": 1},
        "event_type": {"type": "string", "minLength": 1},
        "runtime_type": {"type": "string", "minLength": 1},
        "hook_point": {"type": ["string", "null"]},
        "phase": {"type": ["string", "null"]},
        "trace_id": {"type": ["string", "null"]},
        "parent_event_id": {"type": ["string", "null"]},
        "timestamp": {"type": "string"},
        "actor": _OBJECT,
        "capability": _OBJECT,
        "payload": _OBJECT,
        "context": _OBJECT,
        "risk": _OBJECT,
        "metadata": _OBJECT,
    },
}

RULE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["schema_version", "id", "name"],
    "additionalProperties": False,
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "id": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
        "version": {"type": "string"},
        "enabled": {"type": "boolean"},
        "shadow": {"type": "boolean"},
        "applies_to": _OBJECT,
        "hook": _OBJECT,
        "condition": {"type": ["object", "null"]},
        "detector": _OBJECT,
        "action": _OBJECT,
        "severity": {"type": "string"},
        "telemetry": _OBJECT,
        "testing": _OBJECT,
        "ownership": _OBJECT,
        "archived": {"type": "boolean"},
    },
}

FALLBACK_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["schema_version", "id", "name", "constraints"],
    "additionalProperties": False,
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "id": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
        "enabled": {"type": "boolean"},
        "version": {"type": "string"},
        "applies_to": _OBJECT,
        "triggers": _OBJECT,
        "constraints": {"type": "object", "minProperties": 1},
        "fallback_graph": {"type": "array", "items": _OBJECT},
    },
}

EVAL_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["schema_version", "id", "event", "expected_effect"],
    "additionalProperties": False,
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "id": {"type": "string", "minLength": 1},
        "event": EVENT_SCHEMA,
        "expected_effect": {"type": "string", "minLength": 1},
        "metadata": _OBJECT,
    },
}

CAPABILITY_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["schema_version", "id", "type"],
    "additionalProperties": False,
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "id": {"type": "string", "minLength": 1},
        "type": {"type": "string", "minLength": 1},
        "name": {"type": ["string", "null"]},
        "owner": {"type": ["string", "null"]},
        "compatibility_class": {"type": ["string", "null"]},
        "contracts": _OBJECT,
        "supports": {"type": "array", "items": {"type": "string"}},
        "risk": _OBJECT,
        "permissions": _OBJECT,
        "approval": _OBJECT,
        "fallback": _OBJECT,
        "observability": _OBJECT,
        "enabled": {"type": "boolean"},
        "archived": {"type": "boolean"},
    },
}

SCHEMAS = {
    "rules": RULE_SCHEMA,
    "fallback": FALLBACK_SCHEMA,
    "evals": EVAL_SCHEMA,
    "capabilities": CAPABILITY_SCHEMA,
}


def validate_payload(target_kind: str, data: Any) -> list[str]:
    schema = SCHEMAS.get(target_kind)
    if schema is None:
        return [f"unsupported target_kind: {target_kind}"]

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda err: list(err.path))
    messages = [_format_error(err) for err in errors]
    if messages:
        return messages

    return _validate_cross_fields(target_kind, data)


def _validate_cross_fields(target_kind: str, data: dict[str, Any]) -> list[str]:
    from harnessable.capabilities.schemas import CapabilityProfile
    from harnessable.events.schemas import HarnessEvent
    from harnessable.resilience.fallback_policy_schema import FallbackPolicy
    from harnessable.rules.schemas import HarnessRule

    factories = {
        "rules": lambda: HarnessRule.from_dict(data),
        "fallback": lambda: FallbackPolicy.from_dict(data),
        "evals": lambda: HarnessEvent.from_dict(data["event"]),
        "capabilities": lambda: CapabilityProfile.from_dict(data),
    }
    try:
        factories[target_kind]()
    except Exception as exc:
        return [str(exc)]
    return []


def _format_error(error: Any) -> str:
    location = ".".join(str(item) for item in error.path) or "$"
    return f"{location}: {error.message}"
