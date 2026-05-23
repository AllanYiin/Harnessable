# Rules

Rules are data contracts. They can be added to the registry without changing runtime adapters.

Supported condition syntax:

- `{"field": "runtime_type", "equals": "agent"}`
- `{"field": "payload.text", "contains": "delete"}`
- `{"field": "capability.type", "in": ["TOOL"]}`
- `{"all_of": [...]}`
- `{"any_of": [...]}`
- `{"not": {...}}`

Supported detector types:

- `always_allow`
- `regex`
- `required_field`
- `inferential` placeholder using a fake streaming detector

Shadow rules are evaluated and recorded as contributing decisions, but they do not affect the merged decision.
