from __future__ import annotations

from .effects import DecisionEffect
from .priority import priority
from .schemas import HarnessDecision


AUDIT_REASON_KEYS = {
    "risk_hypotheses",
    "missing_context",
    "affected_stakeholders",
    "misread_paths",
    "required_reviewers",
    "release_constraints",
    "asset_hash",
    "scanner_coverage_gaps",
    "scanner_findings",
    "similarity_matches",
    "provenance_findings",
    "claim_gaps",
    "offer_disclosure_gaps",
    "provenance_gaps",
    "override_expiry",
    "rollback_constraints",
    "incident_links",
}


class DecisionAggregator:
    def merge(self, decisions: list[HarnessDecision], event_id: str) -> HarnessDecision:
        active = [d for d in decisions if not d.shadow]
        if not active:
            merged = HarnessDecision.allow(event_id)
            merged.contributing_decisions = [d.to_dict() for d in decisions]
            return merged
        winner = max(active, key=lambda d: priority(d.effect))
        merged = HarnessDecision.from_dict(winner.to_dict())
        merged.reason = self._merge_audit_reason(merged.reason, decisions)
        merged.contributing_decisions = [d.to_dict() for d in decisions]
        return merged

    @staticmethod
    def is_terminal(effect: DecisionEffect) -> bool:
        return effect in {DecisionEffect.BLOCK, DecisionEffect.ABORT, DecisionEffect.FAIL_SAFE}

    @staticmethod
    def _merge_audit_reason(base: dict, decisions: list[HarnessDecision]) -> dict:
        merged = dict(base)
        for decision in decisions:
            for key in AUDIT_REASON_KEYS:
                value = decision.reason.get(key)
                if not value:
                    continue
                existing = merged.get(key)
                if not existing:
                    merged[key] = list(value) if isinstance(value, list) else value
                    continue
                if isinstance(existing, list) and isinstance(value, list):
                    for item in value:
                        if item not in existing:
                            existing.append(item)
        return merged
