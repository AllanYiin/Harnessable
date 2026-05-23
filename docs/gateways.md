# Gateways

Gateways are the only path from runtime code to external capability.

Lifecycle:

1. Build a `HarnessEvent` before the capability call.
2. Evaluate rules through `HarnessKernel.emit`.
3. Convert `HarnessDecision` to `RuntimeCommand` through `ExecutionGovernor`.
4. Stop, mutate, retry, route, request approval, or execute based on the command.
5. Emit completed or failed event.
6. Record trace, audit, and metrics.

Implemented gateways:

- `ModelGateway`
- `ToolGateway`
- `MemoryGateway`
- `ResourceGateway`
- `AgentGateway`
- `ActionGateway`

`ActionGateway` checks side-effect calls for an idempotency key. Gateway execution also respects capability health states such as `OPEN_CIRCUIT` and `DISABLED`.
