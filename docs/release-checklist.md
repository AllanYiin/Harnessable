# Release Checklist

- [x] Package imports.
- [x] Core schema round-trip tests.
- [x] Rule engine tests.
- [x] Gateway lifecycle tests.
- [x] Capability permission and health tests.
- [x] Fallback safety tests.
- [x] Approval and side-effect tests.
- [x] Chat / agent / multi-agent integration tests.
- [x] Replay regression test.
- [x] Import abuse test.
- [x] Prompt injection sample test.
- [x] Console layout contract test.
- [x] Rule matching performance test.
- [x] Streaming contract test.
- [x] README quickstart documented.
- [x] Known limitations documented.

## Migrated Governance Evidence

Run the narrow evidence below for staged migration work, then run the full
suite before publishing a package release.

| Area | Covering tests |
|---|---|
| Stage 0 migration docs and test mapping | `python -m pytest tests/test_docs_contract.py` |
| Stage 1 runtime command dispatch | `python -m pytest tests/test_runtime_command_dispatch.py tests/test_gateways_and_adapters.py tests/test_streaming_contract.py tests/integration/test_chat_e2e.py` |
| Stage 2 risk schema compatibility | `python -m pytest tests/test_consequence_gate.py tests/regression/test_replay_regression.py tests/test_core_schemas.py` |
| Stage 3 consequence preview bundle | `python -m pytest tests/test_consequence_gate.py tests/regression/test_replay_regression.py` |
| Stage 4 execution evidence policy | `python -m pytest tests/test_execution_evidence_policy.py tests/test_code_execution_harness.py` |
| Stage 5 artifact review governance | `python -m pytest tests/test_artifact_review_policy.py` |
| Stage 6 skill routing, resource, and tool exposure policy | `python -m pytest tests/test_skill_routing.py tests/test_capabilities.py` |
| Stage 7 import, tenant, and secret hardening | `python -m pytest tests/security/test_import_abuse_cases.py tests/test_capabilities.py tests/test_project_fallback_approval.py` |
| Stage 8 documentation closeout | `python -m pytest tests/test_docs_contract.py` |
