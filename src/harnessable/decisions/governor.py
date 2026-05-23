from __future__ import annotations

from .effects import DecisionEffect
from .runtime_command import RuntimeCommand, RuntimeCommandType
from .schemas import HarnessDecision


class ExecutionGovernor:
    def apply(self, decision: HarnessDecision) -> RuntimeCommand:
        mapping = {
            DecisionEffect.ALLOW: RuntimeCommandType.CONTINUE,
            DecisionEffect.OBSERVE: RuntimeCommandType.CONTINUE,
            DecisionEffect.ANNOTATE: RuntimeCommandType.CONTINUE,
            DecisionEffect.WARN: RuntimeCommandType.CONTINUE,
            DecisionEffect.TRANSFORM: RuntimeCommandType.MUTATE,
            DecisionEffect.RETRY: RuntimeCommandType.RETRY,
            DecisionEffect.ROUTE: RuntimeCommandType.ROUTE,
            DecisionEffect.DEGRADE: RuntimeCommandType.ROUTE,
            DecisionEffect.RETURN_CACHED: RuntimeCommandType.CONTINUE,
            DecisionEffect.RETURN_PARTIAL: RuntimeCommandType.CONTINUE,
            DecisionEffect.ASK_USER: RuntimeCommandType.REQUEST_APPROVAL,
            DecisionEffect.REQUIRE_APPROVAL: RuntimeCommandType.REQUEST_APPROVAL,
            DecisionEffect.DISABLE_CAPABILITY: RuntimeCommandType.BLOCK,
            DecisionEffect.ROLLBACK: RuntimeCommandType.ROLLBACK,
            DecisionEffect.BLOCK: RuntimeCommandType.BLOCK,
            DecisionEffect.ABORT: RuntimeCommandType.ABORT,
            DecisionEffect.FAIL_SAFE: RuntimeCommandType.FAIL_SAFE,
        }
        return RuntimeCommand(
            command_type=mapping[decision.effect],
            reason=decision.reason,
            payload={"decision": decision.to_dict()},
        )
