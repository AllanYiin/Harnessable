# Fallback

Fallback uses `FailureSignal`, `FallbackPolicy`, `FallbackGraphPlanner`, and `DegradationBudget`.

The current implementation supports policy matching, ordered fallback steps, disclosure flags, budget exhaustion, and the required safety behavior for unknown side effects: return `REQUIRE_APPROVAL` instead of retrying.

Fallback must not weaken:

- safety policy
- privacy policy
- authorization
- audit requirement
- side-effect approval
- tenant isolation
- secret handling
- truthfulness and disclosure
