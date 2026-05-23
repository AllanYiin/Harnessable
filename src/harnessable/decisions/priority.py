from __future__ import annotations

from .effects import DecisionEffect


EFFECT_PRIORITY: dict[DecisionEffect, int] = {
    DecisionEffect.ALLOW: 0,
    DecisionEffect.OBSERVE: 1,
    DecisionEffect.ANNOTATE: 2,
    DecisionEffect.WARN: 3,
    DecisionEffect.TRANSFORM: 4,
    DecisionEffect.RETRY: 5,
    DecisionEffect.ROUTE: 6,
    DecisionEffect.DEGRADE: 7,
    DecisionEffect.RETURN_CACHED: 8,
    DecisionEffect.RETURN_PARTIAL: 9,
    DecisionEffect.DISABLE_CAPABILITY: 10,
    DecisionEffect.ASK_USER: 11,
    DecisionEffect.ROLLBACK: 12,
    DecisionEffect.REQUIRE_APPROVAL: 13,
    DecisionEffect.BLOCK: 14,
    DecisionEffect.ABORT: 15,
    DecisionEffect.FAIL_SAFE: 16,
}


def priority(effect: DecisionEffect | str) -> int:
    if not isinstance(effect, DecisionEffect):
        effect = DecisionEffect(effect)
    return EFFECT_PRIORITY[effect]
