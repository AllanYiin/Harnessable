# HarnessDiff Core Rule Migration Baseline

This document is the Stage 0 baseline for moving runtime-neutral governance
rules out of HarnessDiff and into Harnessable. It is a migration guide and docs
audit, not a product spec.

## Doc Brief

- Audience: Harnessable and HarnessDiff maintainers implementing the staged
  migration.
- Goal: identify which rules belong in Harnessable core, which code should
  remain a HarnessDiff adapter, and which tests prove the migration did not
  change behavior.
- Version scope: current Harnessable working tree and HarnessDiff checkout at
  `D:\PycharmProjects\HarnessDiff\github_repo`.
- External design reference: policy decision should be separated from policy
  enforcement; telemetry should leave traces, metrics, or logs that prove the
  control path ran.
- Exclusions: HarnessDiff UI layout, local storage, provider clients, launcher,
  and workbench-specific comparison behavior stay in HarnessDiff.

## Boundary Rules

Harnessable owns runtime-neutral governance:

- rule packs, detectors, and decision envelopes;
- versioned governance data contracts;
- capability and tool risk profiles;
- approval, fallback, import preview, and artifact governance policies;
- runtime command semantics.

HarnessDiff owns workbench integration:

- Chat and Agent panes;
- profile selection and NoHarness/Harness comparison;
- provider request construction;
- local run storage and artifact rendering;
- OpenAI tool schema wrappers;
- Docker/container wiring for `standard.code.container_exec`;
- UI chips, banners, and trace display.

The migration target is not to make Harnessable depend on HarnessDiff. The
target is to make HarnessDiff consume Harnessable contracts through thin
adapters.

## Current Inventory

| Domain | Current HarnessDiff evidence | Current Harnessable evidence | Migration target | HarnessDiff after migration |
|---|---|---|---|---|
| Runtime command dispatch | HarnessDiff expects governance decisions to affect run flow. | `docs/architecture.md`, `docs/gateways.md`, `src/harnessable/decisions/governor.py`, `src/harnessable/adapters/chat_adapter.py`. `ChatRuntimeAdapter` currently blocks only `BLOCK`, `ABORT`, and `FAIL_SAFE`. | Stage 1 adds adapter-level handling for `REQUEST_APPROVAL`, `MUTATE`, `RETRY`, `ROUTE`, and `ROLLBACK`. | Observe and display command envelopes; do not reimplement command semantics. |
| Consequence preview rules | `apps/api/app/services/harnessable_control.py` registers `harnessdiff.consequence.*.preview.v1` rules for final-output preview. | `src/harnessable/consequence.py` now exposes `ConsequenceGate.preview_rules()` and `ConsequenceGate.install_preview()` with core `governance.consequence.preview.*` ids; `src/harnessable/risk.py`, `docs/consequence-gate.md`, and `tests/test_consequence_gate.py` cover the contract. | Stage 3 core bundle exists; HarnessDiff should replace private rule registration with `ConsequenceGate.install_preview(...)`. | Call the core bundle and map results to risk chips. |
| Execution evidence policy | `apps/api/app/services/execution_policy.py` builds `requires_execution_evidence` and appends instructions requiring `standard.code.container_exec`. | `src/harnessable/tool_policy/execution_evidence.py`, `docs/execution-evidence-policy.md`, and `tests/test_execution_evidence_policy.py` define the runtime-neutral `ExecutionEvidenceRequirement`; `src/harnessable/code_execution.py` still covers code capability safety. | Stage 4 core policy exists; HarnessDiff wrapper should delegate task detection and requirement building to Harnessable. | Map profile/tool names to the core requirement and preserve run evidence. |
| Artifact review and update governance | `context_builder.py` and `specs/requirements.md` require `artifact_id`, `profile_id`, `base_version`, complete single-page HTML, no default external scripts, and execution evidence for verification claims. | `src/harnessable/state/artifact_review.py`, `docs/artifact-review-policy.md`, and `tests/test_artifact_review_policy.py` define a versioned update review policy. | Stage 5 core policy exists; HarnessDiff should call it before applying artifact patches. | Render artifact warnings and send artifact update payloads through the core policy. |
| Skill routing review | `apps/api/app/services/skill_routing_review.py` exposes an OpenAI tool wrapper. | `src/harnessable/skills/review.py`, `src/harnessable/skills/assembly.py`, `docs/skill-routing.md`, `tests/test_skill_routing.py` already define the fixed JSON contract and deterministic fallback. | Stage 6 makes HarnessDiff consume the core request/result schema directly. | Keep only OpenAI tool schema and trace recording glue. |
| Skill resource hydration | `skill_resource_runtime.py` restricts reads to `references/`, `scripts/`, and `assets/` with list/read tools. | `src/harnessable/skills/resource_policy.py`, `SkillHydrator`, `ContextAssemblyGateway`, and `docs/skill-routing.md` define metadata-first routing, hydration, allowlist, and read limits. | Stage 6 core resource policy exists; HarnessDiff should keep filesystem IO only. | Keep path resolution and local file IO as adapter behavior. |
| Tool risk and baseline gating | `agent_orchestrator.py` and `run_orchestrator.py` derive full tools from `profile.harness_modules["tool_policy"]`, exclude NoHarness tools, and gate subagent/parallel tools. | `src/harnessable/capabilities/*` and `src/harnessable/tool_policy/tool_access.py` define capability profiles and tool exposure decisions. | Stage 6 core tool exposure policy exists; HarnessDiff should provide tool registry facts and consume the decision. | Provide HarnessDiff tool registry facts and consume the core selection decision. |
| Source attribution | `context_builder.py` has `source_map` instructions for URLs, tool metadata, and final answer citations. | Consequence and risk findings have evidence refs, but claim-to-source binding is not yet a core provenance policy. | Stage 8 or later can add a provenance sink after higher-risk governance is core. | Continue rendering links and Sources sections. |
| Import, permission, and secret hardening | HarnessDiff imports skills and local artifacts; report calls out future import risk. | `ImportPreviewStore` rejects root escapes, oversize files, binary-looking files, parse failures, and changed-after-preview applies; `PermissionChecker` has a tenant context seam; `harnessable.secrets` defines secret providers. | Stage 7 core hardening exists; HarnessDiff should surface core import errors and map project/profile context into permission checks. | Feed user-facing import errors and project profile context to Harnessable. |

## Stage Exit Gates

| Stage | Required evidence before moving on |
|---|---|
| Stage 0 | This baseline exists, `docs/test-matrix.md` exists, and docs contract tests require both files. |
| Stage 1 | Runtime adapter conformance tests cover every `RuntimeCommandType` that changes control flow. Streaming behavior still passes. |
| Stage 2 | `RiskContext` and scanner envelopes round-trip with `schema_version`; old payloads still parse. |
| Stage 3 | Harnessable exposes `ConsequenceGate.install_preview()` with core ids. HarnessDiff migration is complete only after it no longer registers private `harnessdiff.consequence.*.preview.*` rules and risk chips still receive structured findings. |
| Stage 4 | Harnessable exposes `ExecutionEvidenceRequirement`; HarnessDiff delegates task detection and requirement building to core while preserving `standard.code.container_exec` as adapter mapping. A final answer that claims verified code/html must be linked to execution evidence or explicitly report missing evidence. |
| Stage 5 | Artifact update policy rejects stale base versions, wrong profile/artifact ids, unsafe HTML script defaults, and unsupported verification claims. |
| Stage 6 | Skill routing review and hydration use Harnessable contracts; HarnessDiff keeps only tool-wrapper and filesystem adapter code. |
| Stage 7 | Import preview rejects oversized, binary, or root-escaping sources before parse/apply; permission and secret provider seams exist. |
| Stage 8 | Test matrix and release checklist name the covering tests for each migrated governance area. |

## Compatibility Rules

- Add new core contracts before replacing HarnessDiff behavior.
- Every new governance payload must include `schema_version`.
- HarnessDiff must run in shadow or preview mode before a migrated policy becomes blocking.
- Existing run artifacts must remain readable; when evidence is missing, adapters should mark it as `unknown`, not invent a pass.
- Harnessable must not import HarnessDiff, FastAPI, Docker, OpenAI provider code, or frontend models.
- HarnessDiff must not keep a second copy of a core rule once a core bundle exists, except as a temporary compatibility shim with a removal stage.

## HarnessDiff Adapter Checklist

When a stage touches HarnessDiff, inspect these paths:

- `apps/api/app/services/harnessable_control.py`
- `apps/api/app/services/execution_policy.py`
- `apps/api/app/services/context_builder.py`
- `apps/api/app/services/run_orchestrator.py`
- `apps/api/app/services/agent_orchestrator.py`
- `apps/api/app/services/chat_tool_runtime.py`
- `apps/api/app/services/skill_routing_review.py`
- `apps/api/app/services/skill_resource_runtime.py`
- `specs/requirements.md`
- relevant backend tests and frontend trace/risk-chip tests

## Open Questions

- The exact core module names for Stage 4 through Stage 6 can still change, but
  they must preserve the boundary in this document.
- HarnessDiff may need a short-lived adapter layer for old run artifacts. That
  shim should be explicitly named and tested so it can be removed later.
- Source attribution is core-like, but it should follow execution evidence and
  artifact governance because it depends on stable evidence envelopes.
