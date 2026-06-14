# Identity and Secret Audit

Stage 21 adds local identity and secret access contracts for multi-project use
without coupling core runtime code to enterprise IAM or a specific KMS.

## Principal

`Principal` records the actor identity used by permission checks:

- `principal_id`
- `role`
- `tenant_id`
- `project_memberships`
- `approval_authorities`

`PermissionContext.from_principal()` maps that identity into the existing
capability permission checker. Capabilities can now require:

- `allowed_roles`
- `allowed_tenant_ids` / `denied_tenant_ids`
- `allowed_purposes` / `denied_purposes`
- `allowed_project_ids`
- `required_approval_authorities`

Fallback selection rejects candidate capabilities that widen role, tenant,
purpose, project, or approval-authority scope compared with the source
capability.

## Secret Access Envelope

`AuditedSecretProvider` wraps any `SecretProvider` and appends a
`SecretAccessEnvelope` for each access. The envelope contains:

- `secret_ref`
- `provider_id`
- `purpose`
- `principal_id`
- `run_id`
- `gateway_call_id`
- `approved`
- `audit_ref`

The envelope never stores the secret value. External KMS, rotation, and hosted
secret managers should be implemented as `SecretProvider` adapters behind this
same audit wrapper.

## Verification

```bash
python -m pytest tests/test_identity_secret_audit.py tests/test_capabilities.py tests/test_docs_contract.py
python -m compileall src
```
