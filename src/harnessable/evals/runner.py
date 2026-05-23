from __future__ import annotations

from .test_case import EvalCase


class EvalRunner:
    def __init__(self, kernel: object) -> None:
        self.kernel = kernel

    def run(self, cases: list[EvalCase]) -> list[dict]:
        results = []
        for case in cases:
            decision = self.kernel.emit_from_dict(case.event)
            results.append({"case_id": case.id, "passed": decision.effect.value == case.expected_effect, "effect": decision.effect.value})
        return results
