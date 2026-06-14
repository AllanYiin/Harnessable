# Agentic Harness Roadmap Spec

This document turns the external agentic harness research findings into a staged
development specification for Harnessable. It extends the existing Stage 0-14
local SDK/CLI/control-plane work without changing the current runtime boundary:
rules produce `HarnessDecision`, `ExecutionGovernor` changes control flow, and
gateways remain the only path to external capabilities.

## Research Gate

### Key Concepts

```text
Agentic harness:
  A control plane around chat, agent, and multi-agent runtimes. It governs model
  calls, tool calls, approvals, replay, audit evidence, fallback, and operator
  workflows instead of trusting each agent implementation to self-police.

Evidence-grade audit artifact:
  A portable, replayable package containing run events, policy decisions, tool
  approvals, artifact hashes, prompt and dataset versions, eval results,
  release gates, and human approval evidence.

Policy-aware gateway:
  A model, tool, MCP, A2A, sandbox, filesystem, or external-action adapter that
  carries risk labels, schema validation, approval routes, tenant/purpose
  constraints, cost budgets, and trace metadata before execution.

Operator console:
  A management surface for platform engineers, security reviewers, and product
  owners. It is not an end-user chat UI. Its primary tasks are trace inspection,
  approval triage, release gating, run comparison, artifact review, and rollout
  monitoring.
```

### External Alignment

```text
NIST AI RMF:
  Supports a lifecycle risk-management framing for AI systems and explicitly
  targets risks to individuals, organizations, and society across design,
  development, use, and evaluation. Harnessable should map future features to
  govern, map, measure, and manage style evidence without claiming certification.

ISO/IEC 42001:
  Frames AI governance as an AI management system with documented policy,
  objectives, controls, transparency, traceability, reliability, risk treatment,
  and continual improvement. Harnessable should export evidence that can support
  such management-system work, not pretend that the SDK alone is an AIMS.

EU AI Act:
  Uses a risk-based approach. High-risk systems require risk assessment,
  logging, documentation, deployer information, human oversight, robustness,
  cybersecurity, and accuracy. Harnessable should support these artifacts and
  operator workflows while avoiding legal-compliance claims by default.

OWASP GenAI Security / LLM Top 10:
  Highlights prompt injection, insecure output handling, sensitive information
  disclosure, insecure plugin design, excessive agency, overreliance, model
  denial of service, supply-chain risk, and model theft. Harnessable should keep
  tool/plugin gateways least-privilege, observable, approval-aware, and
  replayable.
```

Sources:

- NIST AI RMF: <https://www.nist.gov/itl/ai-risk-management-framework>
- ISO/IEC 42001: <https://www.iso.org/standard/42001>
- EU AI Act overview: <https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai>
- OWASP Top 10 for LLM Applications: <https://owasp.org/www-project-top-10-for-large-language-model-applications/>
- MCP tools specification: <https://modelcontextprotocol.io/specification/2025-06-18/server/tools>
- OpenAI Agents SDK tools: <https://openai.github.io/openai-agents-python/tools/>
- A2A protocol specification: <https://a2a-protocol.org/latest/specification/>

### Existing Harnessable Fit

```text
Already present:
  Event model, Rule Engine, HarnessDecision, ExecutionGovernor, gateway
  lifecycle, capability permissions, fallback safety, approvals, trace/audit/
  metrics, eval runner, replay diff, local project/artifact stores, local
  console, import preview/apply, code execution safety contract, and
  PublicationGateway/ConsequenceGate.

Main gap:
  Harnessable has core governance primitives, but not yet the full product
  loop: portable audit packages, policy-aware MCP/A2A/provider adapters,
  trace-to-dataset regression flow, operator console triage, provider usage
  telemetry, full tenant/IAM lifecycle, external secret audit, and deployment
  adapters.

Design implication:
  Future work should extend the control-plane envelope and adapters. It should
  not replace the core with a different agent framework or move policy logic
  into runtime adapters.
```

### Recommended Direction

```text
Recommended:
  Build from the existing governance core outward: evidence package, gateway
  contracts, lineage envelope, provider adapters, replay/eval loop, operator UI,
  identity/secret audit, observability exporters, deployment adapters, and
  vertical harness packs.

Anti-scope:
  Do not prioritize a new agent role abstraction, a LangGraph/Deep Agents clone,
  a historical/cultural blacklist system, fallback paths that bypass governance,
  or a full hosted SaaS before local/self-host contracts are stable.
```

## Technical Spec

### Goals

- Turn Harnessable from a local governance SDK/CLI into a staged, self-hostable
  agentic harness control plane.
- Preserve backward compatibility for existing run artifacts, replay fixtures,
  public APIs, and current local project layouts.
- Add features as narrow, testable contracts before adding richer UI or remote
  deployment surfaces.
- Keep all LLM-generated output on streaming-capable interfaces.
- Keep all external capability access behind gateways.
- Keep all upload/import/config mutation flows preview-before-apply.

### Non-Goals

- Do not build a new general-purpose agent framework or clone existing
  orchestration libraries.
- Do not move direct model, tool, memory, agent, MCP, A2A, scanner, or external
  side-effect calls into runtime adapters.
- Do not encode governance as static risk-word, phrase, market-taboo, or
  historical-incident blacklists.
- Do not let fallback widen permissions, skip approvals, skip audit, skip tenant
  isolation, skip privacy checks, or suppress required disclosure.
- Do not make Harnessable depend on HarnessDiff, FastAPI, React, Docker,
  Kubernetes, OpenAI provider code, LangGraph, LiteLLM, Langfuse, Phoenix, or
  Guardrails in core.
- Do not claim legal compliance, ISO certification, or complete safety coverage
  from built-in sample rules.

### Compatibility Rules

| Area | Rule |
| --- | --- |
| Public APIs | Add optional fields and new modules first. Avoid breaking constructor signatures or serialized shapes. |
| Run artifacts | Existing JSONL and replay fixtures must remain readable. Missing new fields are `unknown`, not failure. |
| Gateway behavior | New adapters emit the same before/after/failed event pattern and respect `ExecutionGovernor`. |
| UI | Console remains local-first until self-host contracts are stable. New operator views must not become a card dashboard. |
| Imports | Any new policy pack, dataset, or external config import must preview, validate, hash, and revalidate before apply. |
| Streaming | Provider integrations must expose streaming paths, including usage metadata when available. |

### Phase Summary

| Phase | Priority | Feature | Outcome |
| --- | --- | --- | --- |
| Stage 15 | Immediate | Roadmap spec baseline | This document, README link, docs contract coverage. |
| Stage 16 | Immediate | Evidence-grade audit package | Portable run evidence bundle with hashes, decisions, approvals, artifacts, eval refs. |
| Stage 17 | Immediate | Policy-aware ToolAnything gateway contracts | MCP/A2A/provider/tool adapter metadata and enforcement contract. |
| Stage 18 | Immediate | Lineage envelope and provider streaming usage | Prompt, dataset, source, model, cost, latency, usage, and provider metadata on run events. |
| Stage 19 | Immediate | Trace-to-dataset-to-replay loop | Promote run traces into eval cases and regression gates. |
| Stage 20 | Immediate | Operator Console 2.0 | Trace explorer, approval queue, run diff, release gate, artifact registry. |
| Stage 21 | Immediate | Tenant/IAM/secret audit contract | Role binding, approval authority, project membership, secret provider audit envelopes. |
| Stage 22 | Medium | Observability exporters and deployment adapters | OpenTelemetry-style export, local DB adapter seam, self-host package contracts. |
| Stage 23 | Medium | Scenario simulator and benchmark suite | Incident replay, synthetic scenarios, trajectory scoring, policy rollout checks. |
| Stage 24 | Long | Compliance export and vertical harness packs | Evidence mappings and reusable coding/research/ops harness profiles. |

## Phase Specs

### Stage 15: Roadmap Spec Baseline

Purpose: make the roadmap explicit before implementation starts.

Deliverables:

- `docs/agentic-harness-roadmap-spec.md`
- README documentation link
- docs contract update

Acceptance criteria:

- The document includes technical spec, plain-language spec, staged
  instructions, non-goals, compatibility rules, acceptance criteria, tests,
  edge cases, and anti-scope gates.
- `tests/test_docs_contract.py` includes this document.
- `python -m pytest tests/test_docs_contract.py` passes.

### Stage 16: Evidence-Grade Audit Package

Purpose: produce a portable evidence artifact for each governed run or release
gate without changing how rules make decisions.

Core model:

```text
AuditPackage
  package_id
  schema_version
  run_id
  project_id
  created_at
  source_trace_refs
  event_refs
  decision_refs
  gateway_call_refs
  approval_refs
  artifact_refs
  artifact_hashes
  eval_refs
  replay_refs
  policy_pack_refs
  lineage_refs
  redaction_summary
  integrity_hash
```

Behavior:

- Export packages from existing trace/audit/artifact/eval stores.
- Do not duplicate large artifact payloads by default; reference them with
  stable ids and hashes.
- Include redaction and omission summaries so absence is explicit.
- Validate package integrity with deterministic hashing.
- Support JSON output first; archive packaging can be a later adapter.

Tests:

- Unit test package serialization and hash stability.
- Regression test that old run artifacts export with `unknown` optional fields.
- Redaction test that secrets and configured sensitive fields are omitted.
- Replay test that a package can identify the replay inputs it was built from.

DoD:

- A CLI command or library API can export one package for a run id.
- Existing replay fixtures still pass.
- Missing fields never invent evidence.

### Stage 17: Policy-Aware ToolAnything MCP/A2A/Provider Gateway Contracts

Purpose: add external protocol readiness without binding core to any specific
MCP, A2A, LiteLLM, or hosted provider implementation. "ToolAnything" means the
same gateway contract covers local function tools, MCP tools, A2A agent skills,
HTTP adapters, provider-hosted tools, shell/sandbox/filesystem tools, and future
tool protocols before execution.

Design goal:

```text
Do not let a tool descriptor be only model-facing prose. Every executable
capability must carry machine-checkable governance metadata, and every gateway
preflight must validate it before runtime code can execute the tool.
```

Core model:

```text
ExternalCapabilityContract
  capability_id
  schema_version
  protocol: function | mcp | a2a | http | provider | sandbox | filesystem
  adapter_id
  source_ref
  source_trust: trusted | untrusted | unknown
  descriptor_hash
  schema_validation
    input_schema_ref
    input_schema_hash
    output_schema_ref
    output_schema_hash
    validator: jsonschema | pydantic | custom | unknown
    strict_input: true | false
    strict_output: true | false
  risk_labels
    side_effect: none | read | write | external_action
    data_classification: public | internal | confidential | secret | unknown
    exfiltration_risk: low | medium | high | unknown
    autonomy_level: model_suggested | model_controlled | human_triggered
    network_scope: none | allowlisted | internet | unknown
    destructive_potential: none | reversible | irreversible | unknown
  approval_route
    required: never | policy | always
    authority: user | project_owner | security_reviewer | admin | custom
    evidence_required
    interruptible: true | false
    resume_token_required: true | false
  cost_budget
    max_calls
    max_runtime_ms
    max_added_cost_usd
    max_tokens
    metering_source: provider_usage | adapter_usage | configured | unknown
    on_exceeded: block | request_approval | warn
  tenant_constraints
    allowed_tenant_ids
    denied_tenant_ids
    project_membership_required
    cross_tenant_routing_allowed: true | false
  purpose_constraints
    allowed_purposes
    denied_purposes
    purpose_evidence_required: true | false
  data_access_scope
    read_scopes
    write_scopes
    secret_refs
    retention_policy
  side_effect_profile
    idempotency_required
    dry_run_supported
    rollback_supported
    preview_required
  audit_required
  fallback_allowed
  compatibility
    legacy_missing_metadata: allow_with_warning | require_approval | block
    deprecated_fields
```

Behavior:

- Add schema objects and validation helpers under a new contract module. The
  model should serialize as optional nested metadata so old `CapabilityProfile`
  payloads continue to load.
- Map contract metadata into `CapabilityProfile.contracts["external_capability"]`
  while continuing to populate existing `risk`, `permissions`, `approval`,
  `fallback`, and `observability` fields for older selectors and rules.
- Normalize MCP `inputSchema`/`outputSchema`, A2A Agent Card security and
  capability metadata, provider hosted-tool metadata, and local function
  signatures into the same `ExternalCapabilityContract` shape. Preserve raw
  adapter metadata in `source_ref` or an audit sidecar, but never trust raw
  annotations without normalization.
- Validate tool arguments before execution and validate structured tool outputs
  when an output schema is present. Output validation failures become gateway
  failures or approval interruptions, not silent text-only fallbacks.
- Gateway preflight must emit `contract_summary` metadata in the before event:
  `protocol`, `descriptor_hash`, `risk_labels`, `approval_route.required`,
  `tenant_constraints`, `purpose_constraints`, `cost_budget`, schema hashes,
  `source_trust`, and any missing-field warnings.
- Treat missing metadata by risk: low-risk read-only tools may `WARN`; tools with
  write, external-action, confidential/secret data, internet network scope, or
  irreversible potential must `REQUIRE_APPROVAL` or `BLOCK` according to policy.
- Fallback selection must compare source and target contracts. A fallback is
  allowed only when it does not broaden tenant access, purpose access, data
  scope, side-effect profile, approval authority, or cost budget.
- Cost budgets are preflight gates and running counters. If provider usage is
  unavailable, store `unknown` plus adapter reason and enforce configured call,
  runtime, and token ceilings instead of pretending to know real cost.

Required validation rules:

| Metadata area | Required for low-risk read-only | Required for high-risk or write/external action | Failure behavior |
| --- | --- | --- | --- |
| Risk labels | `side_effect`, `data_classification` | all risk label fields | warn for low risk; require approval or block for high risk |
| Approval route | optional if policy says no approval | required with authority and evidence fields | require approval or block |
| Cost budget | at least `max_calls` or `max_runtime_ms` | runtime/call ceiling plus cost/token ceiling when metered | warn, request approval, or block by `on_exceeded` |
| Schema validation | input schema or adapter signature hash | input schema hash and output schema hash when structured output exists | block invalid input; fail or interrupt invalid output |
| Tenant constraints | inherit project defaults | explicit allowed/denied or membership rule | deny wrong tenant |
| Purpose constraints | inherit project defaults | explicit allow/deny purpose list or evidence requirement | deny or interrupt missing purpose evidence |

Gateway state flow:

```text
registered -> normalized -> preflight_validating
preflight_validating -> ready
preflight_validating -> warn_missing_metadata
preflight_validating -> approval_required
preflight_validating -> blocked
ready -> executing -> output_validating -> completed
output_validating -> failed_validation
approval_required -> approved -> executing
approval_required -> rejected -> blocked
```

Tests:

- Contract round-trip tests with legacy `CapabilityProfile` payloads missing the
  new optional contract.
- Normalization tests for function, placeholder MCP, placeholder A2A, provider,
  sandbox, and filesystem protocols.
- Schema tests for invalid input, invalid structured output, missing schema
  hash, and untrusted annotation metadata.
- Gateway lifecycle tests proving before events include `contract_summary` and
  failed validation does not execute the tool.
- Permission tests for tenant and purpose constraints, including denied tenant,
  missing project membership, missing purpose evidence, and cross-tenant
  fallback attempts.
- Approval tests for high-risk tools with missing approval route, rejected
  approval, approved resume, and missing required approval evidence.
- Cost-budget tests for max calls, runtime ceiling, token/cost ceiling, and
  unknown provider usage.
- Fallback tests proving route/degrade cannot loosen risk labels, approval
  route, tenant/purpose constraints, data access scope, or cost budget.

DoD:

- No direct MCP/A2A runtime dependency is introduced.
- A future adapter can attach MCP/A2A metadata without private schema drift.
- ToolAnything contracts are visible in gateway event metadata and audit export
  without exposing secret values.
- High-risk tools cannot execute when risk labels, approval route, schema
  validation, tenant constraints, purpose constraints, or cost budget are
  missing beyond policy allowances.
- Existing projects, replay fixtures, and capability selectors remain compatible
  when the new contract is absent.

### Stage 18: Lineage Envelope and Provider Streaming Usage

Purpose: make every governed model/tool result explainable by prompt version,
source refs, dataset refs, model/provider metadata, cost, latency, and usage.

Core model:

```text
LineageEnvelope
  envelope_id
  run_id
  event_id
  prompt_version
  system_policy_version
  dataset_refs
  source_refs
  claim_source_refs
  model_provider
  model_name
  model_revision
  usage
  cost
  latency_ms
  streaming: true | false | unknown
  adapter_metadata
```

Behavior:

- Add optional lineage fields to event metadata or a sidecar store.
- Provider adapters must stream chunks and attach usage when the provider emits
  it.
- If usage is unavailable, store `unknown` and adapter reason.
- Claim-to-source binding remains explicit; do not merge it into generic risk
  findings.

Tests:

- Streaming contract remains valid.
- Provider test double emits chunked output plus usage metadata.
- Missing usage is represented as `unknown`.
- Claim-source refs are preserved through trace and audit export.

DoD:

- Harnessable can show where a generated result came from and what it cost,
  without depending on one model vendor.

### Stage 19: Trace-to-Dataset-to-Replay Regression Loop

Purpose: close the product loop from observed run to reusable regression case.

Workflow:

1. Select run or audit package.
2. Preview candidate eval cases.
3. Redact sensitive fields.
4. Apply to project eval dataset.
5. Run replay against current rules.
6. Compare baseline and candidate decisions.
7. Generate rollout gate report.

Core model:

```text
TracePromotionPreview
  preview_id
  source_run_id
  candidate_cases
  redaction_summary
  policy_versions
  expected_effects
  warnings

RolloutGateReport
  report_id
  baseline_ref
  candidate_ref
  pass
  changed_decisions
  blocked_regressions
  shadow_decisions
```

Tests:

- Preview-before-apply test for trace promotion.
- Changed-after-preview rejection test.
- Replay diff test for changed decisions.
- Shadow rule report test.

DoD:

- One historical run can become a versioned eval case without hand-editing JSON.

### Stage 20: Operator Console 2.0

Purpose: make governance usable by operators without turning the UI into an
end-user chat product.

Primary task:

```text
An operator opens a project, sees runs that need action, inspects evidence, and
approves, rejects, replays, or escalates with a recorded reason.
```

Information architecture:

| Information | Frequency | First viewport | Stage | Display condition | Container | Collapsible |
| --- | --- | --- | --- | --- | --- | --- |
| Action queue | High | Yes | triage | pending approvals, failed gates, high-risk warnings | list/table | No |
| Run summary | High | Yes | triage | selected run | split details pane | No |
| Decision timeline | High | Yes | inspect | selected run | timeline | No |
| Evidence package summary | Medium | Yes | inspect | package exists or can be generated | details panel | Yes |
| Tool/model usage | Medium | No | inspect | usage metadata exists | tab | Yes |
| Artifact registry | Medium | No | inspect/apply | project has artifacts | tab | Yes |
| Replay diff | Medium | No | validate | replay result exists | tab | Yes |
| Raw JSON | Low | No | debug | user expands advanced view | drawer | Yes |
| Reference docs | Low | No | help | user opens help | drawer/link | Yes |

Content audit:

| Category | Content |
| --- | --- |
| must-see-now | action queue, selected run status, highest priority decision, required next action |
| next-step-only | approval evidence form, replay command, export audit package |
| error-only | failed validation, missing evidence, stale preview, gateway unavailable |
| on-demand-reference | raw event JSON, schema docs, external framework links |
| keep-off-first-viewport | long policy explanations, complete artifact contents, historical charts |

State model:

```text
idle -> project_loaded -> run_selected -> action_required
action_required -> approval_previewed -> approval_applied
action_required -> replay_previewed -> replay_applied
action_required -> audit_exported
any -> error
error -> recovered | idle
```

UI rules:

- List-first, not summary-card-first.
- No nested cards.
- Preserve graph aspect ratio.
- All actions that mutate project state use preview/apply.
- Long running operations show phase, current item, percentage when available,
  and final artifact path.

Tests:

- Static layout contract test for first-viewport task model.
- UI state fixture tests for empty, pending approval, replay diff, export
  complete, and error states.
- Accessibility smoke for button labels and keyboard-visible actions.

DoD:

- Operators can perform one complete approve/replay/export flow locally.

### Stage 21: Tenant/IAM/Secret Audit Contract

Purpose: turn existing tenant and secret seams into enforceable contracts before
remote or hosted deployments are added.

Core model:

```text
Principal
  principal_id
  role
  tenant_id
  project_memberships
  approval_authorities

SecretAccessEnvelope
  secret_ref
  provider_id
  purpose
  principal_id
  run_id
  gateway_call_id
  approved
  audit_ref
```

Behavior:

- Add project membership and approval authority checks.
- Add secret access audit envelopes for provider integrations.
- Keep secret values out of traces and audit packages.
- Add external KMS/rotation as adapter interfaces, not core dependencies.

Tests:

- Permission denied for wrong tenant, wrong role, missing project membership,
  and missing approval authority.
- Secret access emits audit metadata without storing secret values.
- Fallback cannot route to a capability requiring broader authority.

DoD:

- Multi-project local usage can model who may approve or execute a capability.

### Stage 22: Observability Exporters and Deployment Adapters

Purpose: make Harnessable self-host friendly while keeping core small.

Deliverables:

- OpenTelemetry-style trace exporter interface.
- JSONL and local file exporter parity tests.
- Optional remote database store interface.
- Docker/Kubernetes deployment examples as adapter documentation, not runtime
  requirements.
- Health, backup, retention, and migration notes.

Tests:

- Exporter contract tests.
- Store adapter compatibility tests.
- Migration dry-run test for project schema versions.

DoD:

- Teams can integrate Harnessable traces into existing observability systems
  without adopting a hosted SaaS.

### Stage 23: Scenario Simulator and Benchmark Suite

Purpose: create reusable scenario and benchmark loops from incidents, policy
changes, and synthetic stress cases.

Deliverables:

- Scenario schema.
- Synthetic trace generator for safe non-sensitive cases.
- Trajectory scoring hooks.
- Policy rollout benchmark report.
- Incident replay pack conventions.

Tests:

- Scenario schema validation.
- Deterministic seed behavior.
- Benchmark report includes limitations when coverage is weak.

DoD:

- A policy change can be evaluated against historical and synthetic scenarios
  before rollout.

### Stage 24: Compliance Export and Vertical Harness Packs

Purpose: package reusable governance workflows without making compliance claims
or locking core to one vertical.

Deliverables:

- Evidence mapping export for NIST AI RMF style functions.
- ISO/IEC 42001 support matrix export with "supports evidence for" language.
- EU AI Act high-risk support checklist export with "not legal advice" warning.
- Vertical packs for coding, research, and ops agents.

Tests:

- Export contains source evidence refs and limitations.
- Vertical packs install through preview/apply.
- Built-in pack claims do not exceed test evidence.

DoD:

- A team can select a vertical pack and generate governance evidence while
  preserving provider-neutral core behavior.

## Plain-Language Spec

Harnessable already has the right foundation: it watches agent activity, runs
rules, makes decisions, routes work through gateways, records traces, and can
replay behavior. The next step is not to make agents more autonomous. The next
step is to make agent work easier to inspect, approve, replay, and audit.

The first priority is evidence. When an AI agent uses a tool, asks for approval,
publishes something, changes an artifact, or triggers a policy decision,
Harnessable should be able to export a clear evidence package. That package
should answer: what happened, what rule decided it, what tool was used, what
human approved it, what artifact changed, what source or dataset was involved,
and whether the same case can be replayed.

The second priority is safe external access. MCP, A2A, model providers, shell,
filesystem, sandbox, and HTTP tools should all enter through the same
ToolAnything gateway style. Each tool should describe its risk, required
approval, tenant limits, purpose limits, schema checks, cost limits, data access,
and audit requirements before it runs.

The third priority is a practical operator console. The console should help a
human reviewer see pending actions, inspect a run, review evidence, approve or
reject with a reason, replay a failure, and export an audit package. It should
not become a marketing dashboard or a general chat UI.

The medium-term work is about integration: exporting traces to existing
observability tools, supporting self-host deployment, simulating scenarios, and
running benchmark gates. The long-term work is packaging these capabilities into
compliance-support exports and vertical harness packs for coding, research, and
ops agents.

The line that must not be crossed: do not bypass Harnessable's governance
boundaries. Fallbacks cannot skip safety. Runtime adapters cannot call external
tools directly. The project should not become a blacklist engine, a clone of an
agent framework, or a hosted SaaS before the local and self-host contracts are
stable.

## Acceptance Criteria

Global acceptance criteria:

- Every new external capability path goes through a gateway.
- Every mutating import or config change uses preview/apply.
- Every LLM provider integration has a streaming path.
- Every new serialized field is optional or versioned for compatibility.
- Every new operator action records audit evidence.
- Every stage includes focused tests and does not rely only on manual review.
- Every limitation is explicit when evidence is absent.
- No stage introduces a direct dependency that violates the non-goals.

Gherkin examples:

```gherkin
Feature: Evidence package export
  Scenario: Export a run with existing artifacts
    Given a project has a completed governed run
    When the operator exports an audit package for the run
    Then the package contains event refs, decision refs, approval refs, artifact hashes, and an integrity hash
    And missing optional lineage fields are marked as unknown
    And secret values are not present

Feature: Policy-aware gateway contract
  Scenario: A high-risk MCP tool is missing approval metadata
    Given a tool capability declares protocol mcp and high risk labels
    And the capability has no approval route
    When the gateway preflight evaluates the tool call
    Then the decision is WARN or REQUIRE_APPROVAL according to policy
    And the runtime adapter does not execute the tool directly

  Scenario: A ToolAnything fallback would broaden tenant access
    Given a source tool contract allows only tenant_a
    And a fallback tool contract allows tenant_a and tenant_b
    When the gateway evaluates the fallback route
    Then the fallback is blocked
    And the audit event records tenant constraint broadening

  Scenario: A structured tool result fails output schema validation
    Given a provider tool contract includes an output schema hash
    And the tool returns structured content that does not match the schema
    When the gateway validates the result
    Then the call is marked failed_validation
    And the invalid result is not passed to the model as trusted content

Feature: Trace promotion
  Scenario: Promote a failed run to an eval case
    Given a failed run exists in the trace store
    When the operator previews trace promotion
    Then Harnessable shows candidate eval cases and redaction warnings
    When the operator applies the preview without source changes
    Then a versioned eval case is written
    And replay can diff it against the baseline
```

## Edge And Abuse Cases

| Case | Expected handling |
| --- | --- |
| Old run artifact lacks lineage fields | Export with `unknown` values and compatibility warnings. |
| Trace contains secrets | Redact and include redaction summary; never export raw secret values. |
| User approves high-risk action without evidence | Reject approval or keep run interrupted until required evidence exists. |
| Fallback route is cheaper but has broader permissions | Block as unsafe fallback target. |
| MCP/A2A adapter supplies no schema hash | Warn or require approval based on risk labels. |
| Tool descriptor has trusted-looking annotations from an untrusted server | Preserve raw metadata for audit, but normalize as untrusted and require policy checks. |
| Cost budget is missing for a network or provider-hosted tool | Require approval or block before execution, depending on policy. |
| Tool purpose is absent but project requires purpose evidence | Interrupt for purpose evidence; do not infer purpose from prompt text alone. |
| Provider usage metadata is unavailable | Store `unknown` plus adapter reason; do not estimate as real usage. |
| Operator tries to apply stale trace-promotion preview | Reject and require a new preview. |
| Compliance export lacks enough evidence | Generate limitations; do not claim compliance. |
| Vertical pack imports unsafe tool defaults | Preview fails or requires explicit review before apply. |

## Codex / Claude Code Staged Plan

### Stage 15 Instructions

Codex:

```text
Implement Stage 15 only. Add the agentic harness roadmap spec to docs, link it
from README, and add it to docs contract tests. Do not change runtime code.
Run python -m pytest tests/test_docs_contract.py.
```

Claude Code:

```text
Work only on documentation for Stage 15. Create/update the roadmap spec,
README docs index, and docs existence test. Preserve existing formatting and
do not add dependencies. Verify with the docs contract test.
```

DoD:

- Roadmap spec exists.
- README links the spec.
- Docs contract test includes the spec and passes.

### Stage 16 Instructions

Codex:

```text
Implement an AuditPackage model and export API using existing trace, audit,
artifact, approval, eval, and replay stores. Keep fields optional for backward
compatibility. Add serialization, integrity hash, redaction summary, and tests.
Do not change decision semantics.
```

Claude Code:

```text
Add the audit package as a sidecar export feature. Reuse existing stores and
avoid large payload duplication. Missing data must be unknown, not fabricated.
Add focused tests for old artifact compatibility, hashing, and redaction.
```

DoD:

- Export API or CLI exists.
- Old runs export successfully.
- Tests prove hash stability and secret redaction.

### Stage 17 Instructions

Codex:

```text
Add policy-aware external capability contracts for function, mcp, a2a, http,
provider, sandbox, and filesystem protocols. Treat this as the ToolAnything
contract layer: every executable tool capability must support risk labels,
approval route, cost budget, schema validation metadata, tenant constraints,
and purpose constraints before execution.

Task scope:
- Add optional contract schemas without breaking existing CapabilityProfile
  serialization.
- Map contracts into CapabilityProfile.contracts["external_capability"] and
  keep existing risk/permissions/approval/fallback fields populated for
  backward compatibility.
- Add normalization helpers for local function tools and placeholder MCP/A2A
  descriptors. Do not add real MCP/A2A network dependencies.
- Emit a contract_summary on gateway before events.
- Add preflight validation for missing high-risk metadata, schema hashes,
  tenant/purpose constraints, approval route, and cost budgets.
- Add fallback comparison so fallback cannot broaden risk, authority, tenant,
  purpose, data scope, side-effect profile, or cost budget.

Tests:
- Round-trip old and new capability payloads.
- Validate invalid input and invalid structured output.
- Assert high-risk missing approval route requires approval or blocks.
- Assert wrong tenant/purpose is denied.
- Assert fallback broadening is blocked.
- Assert unknown provider usage is recorded as unknown, not estimated.
```

Claude Code:

```text
Model protocol metadata and validation first. Implement the ToolAnything
contract as optional structured metadata, then add gateway tests that prove
contract metadata is emitted and fallback cannot loosen constraints. Preserve
old replay fixtures and existing CapabilityProfile users.
```

DoD:

- Contract schema round-trips.
- Gateway events include contract metadata.
- Fallback and permission tests pass.

### Stage 18 Instructions

Codex:

```text
Add a LineageEnvelope sidecar or optional event metadata for prompt version,
dataset refs, source refs, provider metadata, usage, cost, latency, and
streaming status. Add a streaming provider test double. Do not bind core to one
provider.
```

Claude Code:

```text
Preserve the existing streaming contract. Attach usage when available and store
unknown when unavailable. Keep claim-source binding explicit and testable.
```

DoD:

- Streaming tests still pass.
- Provider usage is captured when emitted.
- Missing usage is explicit.

### Stage 19 Instructions

Codex:

```text
Build trace promotion: preview candidate eval cases from a run, redact, apply,
and replay against baseline. Add rollout gate reports. All writes must be
preview/apply.
```

Claude Code:

```text
Reuse EvalCase and ReplayEngine. Add a preview object and changed-after-preview
protection. Test promotion, replay diff, and shadow rule reporting.
```

DoD:

- One run can become an eval case.
- Replay diff report identifies changed decisions.
- Stale previews are rejected.

### Stage 20 Instructions

Codex:

```text
Upgrade the local Console for operator workflows: action queue, run details,
decision timeline, evidence package export, approval form, replay diff, and
artifact registry. Keep it local-first, list-first, responsive, and
aspect-ratio safe.
```

Claude Code:

```text
Start from task model and states. Add UI fixtures for empty, pending approval,
replay diff, export complete, and error states. Do not create a card dashboard.
```

DoD:

- Operator can inspect a run, approve/reject with evidence, replay, and export.
- UI contract tests cover the key states.

### Stage 21 Instructions

Codex:

```text
Add Principal, project membership, approval authority, and secret access audit
contracts. Keep external KMS as an adapter seam. Ensure secret values never
enter traces or audit packages.
```

Claude Code:

```text
Extend permission checks carefully without breaking existing tenant-id behavior.
Add tests for role, tenant, project membership, approval authority, and secret
audit metadata.
```

DoD:

- Wrong tenant/role/project/authority is denied.
- Secret audit envelopes contain metadata only.

### Stage 22 Instructions

Codex:

```text
Add observability exporter interfaces and self-host adapter docs. Keep exporter
dependencies optional. Add contract tests for JSONL and OpenTelemetry-style
export shapes.
```

Claude Code:

```text
Implement exporter seams before deployment examples. Do not make Docker,
Kubernetes, or remote DB required for core tests.
```

DoD:

- Exporter contract is tested.
- Deployment docs describe optional adapters and limitations.

### Stage 23 Instructions

Codex:

```text
Add scenario schema, deterministic synthetic scenario generation, trajectory
scoring hooks, and policy rollout benchmark reports. Include limitation fields
when benchmark coverage is weak.
```

Claude Code:

```text
Keep generated scenarios safe and non-sensitive by default. Add deterministic
seed tests and avoid claiming quality improvements without benchmark evidence.
```

DoD:

- Scenario schema validates.
- Benchmark report is reproducible and limitation-aware.

### Stage 24 Instructions

Codex:

```text
Add compliance-support exports and vertical harness packs. Use "supports
evidence for" wording. Do not claim legal compliance or certification. Packs
must install through preview/apply.
```

Claude Code:

```text
Create evidence mapping exports for NIST AI RMF style functions, ISO/IEC 42001
support, and EU AI Act high-risk support checklists. Add coding, research, and
ops pack skeletons with tests.
```

DoD:

- Exports include evidence refs and limitations.
- Packs preview/apply successfully.
- Claims stay within tested evidence.
