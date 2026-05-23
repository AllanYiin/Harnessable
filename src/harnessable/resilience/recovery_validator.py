from __future__ import annotations


class RecoveryValidator:
    def validate(self, result: object) -> bool:
        if isinstance(result, dict) and result.get("guardrails_passed") is False:
            return False
        return result is not None
