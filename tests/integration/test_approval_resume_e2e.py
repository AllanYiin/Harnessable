from harnessable.approvals import ApprovalManager, ApprovalStatus, InterruptionStore, ResumeController, RunInterruption
from harnessable.state import RunCheckpoint


def test_approval_resume_e2e():
    approvals = ApprovalManager()
    request = approvals.create("run", "evt")
    interruption = RunInterruption(request.id, RunCheckpoint("run", "evt", {"cursor": 1}))
    store = InterruptionStore()
    store.save(interruption)
    approvals.approve(request.id)
    result = ResumeController(store).resume_if_approved(store.get(request.id), ApprovalStatus.APPROVED)
    assert result["resumed"] is True
