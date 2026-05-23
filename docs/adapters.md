# Adapters

Runtime adapters map native runtime concepts into `HarnessEvent`.

Implemented reference adapters:

- `ChatRuntimeAdapter`
- `AgentRuntimeAdapter`
- `MultiAgentRuntimeAdapter`

Adapter rules:

- Do not embed rule logic in adapters.
- Do not call external tools directly from adapters.
- Model output must use streaming.
- Handoffs are explicit `AGENT_HANDOFF_REQUESTED` events.

To add a runtime:

1. Implement `RuntimeAdapter`.
2. Convert native inputs/actions into `HarnessEvent`.
3. Use kernel decisions and governor commands to drive the runtime.
4. Add integration tests proving common rules still apply.
