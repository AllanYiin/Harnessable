from __future__ import annotations

from harnessable.core.errors import PolicyViolationError

from .failure_signal import FailureCategory, FailureLayer, FailureSignal


class FailureClassifier:
    def classify(self, exc: Exception, run_id: str, event_id: str, layer: FailureLayer = FailureLayer.RUNTIME) -> FailureSignal:
        text = str(exc).lower()
        if isinstance(exc, TimeoutError) or "timeout" in text:
            category = FailureCategory.TIMEOUT
        elif "rate" in text:
            category = FailureCategory.RATE_LIMIT
        elif isinstance(exc, PermissionError) or isinstance(exc, PolicyViolationError):
            category = FailureCategory.PERMISSION
        elif "unknown" in text and "side" in text:
            category = FailureCategory.SIDE_EFFECT_UNKNOWN
        else:
            category = FailureCategory.UNKNOWN
        retryable = category not in {FailureCategory.PERMISSION, FailureCategory.SIDE_EFFECT_UNKNOWN}
        return FailureSignal(run_id=run_id, event_id=event_id, layer=layer, category=category, retryable=retryable)
