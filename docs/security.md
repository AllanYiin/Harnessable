# Security

Security boundaries:

- Tool and action gateways are deny/stop points.
- Side-effect actions require idempotency keys.
- Unknown side-effect state must not be retried automatically.
- Imports are previewed before apply.
- Audit logging defaults to metadata-only.
- Fallback must not degrade safety, privacy, authorization, audit, side-effect approval, tenant boundaries, secret handling, or disclosure.

Built-in rules are samples. They do not claim complete compliance coverage.
