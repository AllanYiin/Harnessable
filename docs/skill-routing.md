# Skill Routing

Harnessable treats skills as context resources, not as runtime shortcuts.

The skill routing flow is metadata-first:

1. Build a `SkillIndex` from low-cost `SkillManifest` records.
2. Run `SkillSelector` against manifest metadata only.
3. Hydrate summaries or full `SKILL.md` content only after selection.
4. Enforce `SkillContextBudget` and emit `CONTEXT_BUDGET_EXCEEDED` when selection or hydration exceeds budget.
5. Call the `skill_routing_review` tool when selected skills are empty but `SkillUndertriggerAudit` finds risky copywriting, public release, persuasion, sensitive-date, or humanization context, or when top candidate scores are too close.
6. Run `SkillUndertriggerAudit` before final output when a risky task still has no selected skills.

`ContextAssemblyGateway` is the gateway boundary for this flow. Runtime adapters should not read skill files directly. They should call the gateway and let the gateway emit context assembly, budget, and audit-visible events.

Prompt construction should keep stable manifest metadata before dynamic user task content. This preserves prompt-cache friendliness while keeping full skill text out of the selector stage.

`skill_routing_review` must return fixed JSON, not free-form prose:

- `decision`: `none`, `keep`, `add`, or `replace`
- `selected_skill_ids`: ordered skill ids to hydrate
- `confidence`: number from `0` to `1`
- `reasons`: short audit reasons
- `should_hydrate`: whether the assembler should hydrate the returned skills

The core package includes a deterministic fallback review tool for tests and local policy. Production runtimes can replace it with a model-backed tool as long as they validate the same JSON schema.
