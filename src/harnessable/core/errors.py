from __future__ import annotations


class HarnessableError(Exception):
    """Base error with a stable code for callers and tests."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class ValidationError(HarnessableError):
    def __init__(self, message: str) -> None:
        super().__init__("VALIDATION_ERROR", message)


class NotFoundError(HarnessableError):
    def __init__(self, message: str) -> None:
        super().__init__("NOT_FOUND", message)


class PolicyViolationError(HarnessableError):
    def __init__(self, message: str) -> None:
        super().__init__("POLICY_VIOLATION", message)


class ApprovalRequiredError(HarnessableError):
    def __init__(self, message: str) -> None:
        super().__init__("APPROVAL_REQUIRED", message)
