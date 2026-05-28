# Security

Security boundaries:

- Tool and action gateways are deny/stop points.
- Side-effect actions require idempotency keys.
- Unknown side-effect state must not be retried automatically.
- Imports are previewed before apply.
- Audit logging defaults to metadata-only.
- Externally visible publication should pass through `ConsequenceGate`; missing release context is treated as risk, not as approval.
- Consequence approvals can require counter-evidence such as opened artifacts and an approval reason.
- Fallback must not degrade safety, privacy, authorization, audit, side-effect approval, tenant boundaries, secret handling, or disclosure.

Built-in rules are samples. They do not claim complete compliance coverage.
