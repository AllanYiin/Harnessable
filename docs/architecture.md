# Architecture

`harnessable` keeps runtime-specific code out of the policy path.

Flow:

1. Runtime adapters convert chat, agent, and multi-agent activity into `HarnessEvent`.
2. `HarnessKernel.emit()` records the event and asks `RuleEngine` for a `HarnessDecision`.
3. `PluginManager` runs `before_emit` and `after_decision` hooks around the rule decision path.
4. `RuleEngine` matches rules, evaluates conditions, runs detectors, and aggregates decisions by priority.
5. `ExecutionGovernor` converts the decision into a runtime command.
6. Gateways execute model/tool/memory/resource/agent/action work only after the command allows it, with `before_gateway_call` and `after_gateway_call` plugin hooks around execution.
7. Fallback and approval modules model resilience and interruption as explicit state, not ad hoc `try/except`.

Non-goals in this implementation:

- No hosted cloud service.
- No real model provider.
- No remote database.
- No enterprise IAM.
- No full local console UI yet.
