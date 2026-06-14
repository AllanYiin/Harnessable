# Known Limitations

- No real LLM provider integration.
- No remote database adapter.
- No hosted cloud service.
- No enterprise IAM.
- Secret provider abstraction exists, but there is no external KMS, rotation, or audit integration yet.
- Permission checks support a tenant-id seam, but there is no enterprise IAM or full tenant lifecycle model yet.
- Console is a local static management surface, not a full SaaS UI.
- Inferential detectors are represented by a fake streaming test double.
- Fallback execution planning is implemented, but real external route execution is left to gateway integrations.
- Built-in rules are baseline samples, not a complete safety or compliance policy.
