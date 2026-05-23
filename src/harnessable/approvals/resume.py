from __future__ import annotations

from .approval_manager import ApprovalStatus
from .interruption import InterruptionStore, RunInterruption


class ResumeController:
    def __init__(self, interruptions: InterruptionStore) -> None:
        self.interruptions = interruptions

    def resume_if_approved(self, interruption: RunInterruption, status: ApprovalStatus) -> dict:
        if status == ApprovalStatus.APPROVED:
            interruption.status = "RESUMED"
            return {"resumed": True, "checkpoint": interruption.checkpoint}
        interruption.status = "BLOCKED"
        return {"resumed": False, "blocked": True}
