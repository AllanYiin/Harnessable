# Test Matrix

This matrix maps release checklist items and the HarnessDiff migration baseline
to concrete tests. Treat missing or narrow evidence as work to schedule, not as
proof that the requirement is covered.

## How To Use

Run the narrow tests for the stage being changed. Before release, run the full
test suite and update this matrix when a new governance area is added.

```powershell
python -m pytest tests/test_docs_contract.py
python -m pytest tests/test_runtime_command_dispatch.py tests/test_gateways_and_adapters.py tests/test_streaming_contract.py
python -m pytest tests/test_consequence_gate.py tests/regression/test_replay_regression.py
python -m pytest tests/test_code_execution_harness.py
python -m pytest tests/test_execution_evidence_policy.py
python -m pytest tests/test_artifact_review_policy.py
python -m pytest tests/test_skill_routing.py
python -m pytest tests/security tests/resilience
```

## Release Checklist Mapping

| Release checklist item | Current test evidence | Coverage status | Notes |
|---|---|---|---|
| Package imports | `tests/test_package_import.py` | Covered | Should be run after public exports change. |
| Core schema round-trip | `tests/test_core_schemas.py`, `tests/test_validation_and_plugins.py`, `tests/test_consequence_gate.py` | Covered | Risk context and scanner result schema version coverage lives in consequence gate tests. |
| Rule engine tests | `tests/test_rule_engine.py`, `tests/perf/test_rule_matching_perf.py` | Covered | New rule bundles should add exact rule id expectations. |
| Gateway lifecycle tests | `tests/test_gateways_and_adapters.py`, `tests/test_runtime_command_dispatch.py` | Covered | Runtime command dispatch is covered at the chat adapter boundary; gateway-specific retry/route policies still need dedicated tests when gateway behavior changes. |
| Capability permission and health tests | `tests/test_capabilities.py` | Covered | Stage 6 tool access policy tests cover tool-policy-gated power tools. |
| Fallback safety tests | `tests/test_project_fallback_approval.py`, `tests/integration/test_fallback_e2e.py`, `tests/resilience/test_side_effect_unknown.py` | Covered | Keep safety-boundary degradation tests when route/retry changes. |
| Approval and side-effect tests | `tests/test_consequence_gate.py`, `tests/integration/test_approval_resume_e2e.py` | Covered | Stage 1 request-approval dispatch must add adapter evidence. |
| Chat / agent / multi-agent integration | `tests/integration/test_chat_e2e.py`, `tests/integration/test_agent_tool_e2e.py`, `tests/integration/test_multi_agent_e2e.py` | Covered | Add HarnessDiff adapter smoke tests in the HarnessDiff repo when stages touch it. |
| Replay regression | `tests/regression/test_replay_regression.py` | Covered | Stage 2 schema changes must preserve replay fixtures. |
| Import abuse | `tests/security/test_import_abuse_cases.py` | Covered | Stage 7 covers invalid parse, source root allowlist, size limit, binary sniffing, and changed-after-preview rejection. |
| Prompt injection sample | `tests/security/test_prompt_injection_cases.py` | Covered | Keep guardrail behavior separate from HarnessDiff UI instructions. |
| Console layout contract | `tests/ui/test_console_layout_contract.py` | Covered | Not part of core rule migration unless console displays new policy states. |
| Rule matching performance | `tests/perf/test_rule_matching_perf.py` | Covered | Add new rule packs without broad unbounded scans. |
| Streaming contract | `tests/test_streaming_contract.py` | Covered | Stage 1 must prove command dispatch does not break streaming. |
| README quickstart documented | `README.md`, `tests/test_docs_contract.py` | Covered | Update only when public commands change. |
| Known limitations documented | `docs/known-limitations.md`, `tests/test_docs_contract.py` | Covered | Tenant and secret-provider boundaries are documented after Stage 7. |

## Migration Coverage Matrix

| Migration area | Harnessable evidence today | HarnessDiff evidence today | Required next test |
|---|---|---|---|
| Runtime command dispatch | `ExecutionGovernor`, `RuntimeCommandType`, `ChatRuntimeAdapter`, `tests/test_runtime_command_dispatch.py` | HarnessDiff relies on run-flow effects from governance modules. | Stage 1 covers continue, block, approval, mutate, retry, route, rollback, abort, and fail-safe at the chat adapter boundary. |
| Consequence preview bundle | `ConsequenceGate.preview_rules()`, `ConsequenceGate.install_preview()`, versioned `RiskContext`, consequence detectors, replay fixtures, `tests/test_consequence_gate.py` | `harnessable_control.py` installs the core `governance.consequence.preview.*.v1` bundle when Harnessable exposes it, with a legacy fallback for older core versions. | Stage 3 core and HarnessDiff adapter smoke are covered. |
| Execution evidence policy | `ExecutionEvidenceRequirement`, `tests/test_execution_evidence_policy.py`, `CodeExecutionHarness` capability safety tests | `execution_policy.py` wrapper delegates to Harnessable core and still maps to `standard.code.container_exec` | Stage 4 core and HarnessDiff wrapper are covered by `tests/test_execution_evidence_policy.py` and HarnessDiff `tests/api/test_execution_policy.py`. |
| Artifact review governance | `ArtifactStore` versioning tests and `tests/test_artifact_review_policy.py` | `artifact_review` prompt/spec requirements in HarnessDiff | Stage 5 core policy covers stale base version, wrong profile id, wrong artifact id, unsafe external script, and verification-claim rejection tests. |
| Skill routing review | Core fixed JSON contract and deterministic fallback in `tests/test_skill_routing.py` | HarnessDiff OpenAI wrapper in `skill_routing_review.py` | Stage 6: wrapper normalizes to/from Harnessable request/result without private schema drift. |
| Skill resource hydration | `SkillContextAssembler`, `ContextAssemblyGateway`, `SkillHydrator`, and core skill resource policy tests | HarnessDiff resource list/read tools with `references/`, `scripts/`, `assets/` allowlist | Stage 6 core policy covers allowlist, max chars, selected-skill requirement, and adapter path resolution. |
| Tool risk and baseline gating | Capability profiles, permissions, selector, health, and `build_tool_exposure_decision` | `tool_access_policy.py` delegates HarnessDiff subagent/parallel/code-tool exposure decisions to Harnessable core. | Stage 6 core policy and HarnessDiff targeted run tests are covered. |
| Import hardening | Import preview/apply and import abuse tests cover root allowlist, max bytes, binary sniffing, parse fail-fast, and apply-after-invalid rejection | HarnessDiff skill import uses a separate zip/base64 workflow with existing path traversal tests; core import hardening stays in Harnessable until a shared import adapter exists. | Stage 7 core hardening is covered; do not wire a mismatched import model into HarnessDiff without an adapter contract. |
| Source attribution | Evidence refs in risk findings and artifact verification evidence refs | `source_map` prompt instructions, final answer source rendering, and artifact verification refs | Stage 8 keeps claim/source binding as an explicit future envelope-level contract instead of silently merging it with unrelated governance rules. |

## Minimum Stage 0 Verification

Stage 0 is complete only when:

- `docs/migration-harnessdiff-core-rules.md` exists and names the current
  HarnessDiff adapter files.
- `docs/test-matrix.md` exists and maps every release checklist item to tests.
- `tests/test_docs_contract.py` requires both new docs.
- `python -m pytest tests/test_docs_contract.py` passes.
