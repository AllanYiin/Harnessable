import asyncio
import json
from pathlib import Path
from typing import Any

try:
    from _bootstrap import add_src_to_path
except ModuleNotFoundError:
    from examples._bootstrap import add_src_to_path

add_src_to_path()

from harnessable import ConsequenceGate, HarnessKernel, RiskContext
from harnessable.approvals import ApprovalManager
from harnessable.events import EventType, HarnessEvent
from harnessable.gateways import GatewayContext, PublicationGateway, PublicationRequest


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "template_conversation_change.json"


def load_template() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def print_decision(label: str, decision: object) -> None:
    reason = decision.reason
    print(f"\n== {label} ==")
    print(f"  effect: {decision.effect.value}")
    print(f"  reason: {reason.get('code', 'n/a')}")
    for key in ("missing_context", "scanner_coverage_gaps", "affected_stakeholders", "misread_paths", "required_reviewers"):
        value = reason.get(key)
        if value:
            print(f"  {key}: {value}")


def print_gateway_result(label: str, result: object) -> None:
    print(f"\n== {label} ==")
    print(f"  gateway ok: {result.ok}")
    if result.ok:
        print(f"  gateway value: {result.value}")
        return
    command = result.command
    decision = command.payload["decision"] if command else {}
    print(f"  runtime command: {command.command_type.value if command else 'ERROR'}")
    print(f"  decision effect: {decision.get('effect')}")
    print(f"  missing_context: {decision.get('reason', {}).get('missing_context')}")
    print(f"  scanner_coverage_gaps: {decision.get('reason', {}).get('scanner_coverage_gaps')}")


async def main() -> None:
    template = load_template()
    kernel = HarnessKernel()
    ConsequenceGate.install(kernel)

    change = template["requested_change"]
    print(f"Loaded template conversation: {template['conversation_id']}")
    print(f"Requested change: {change['id']}")

    draft_decision = kernel.emit(
        HarnessEvent(
            event_id="evt_conversation_change_draft",
            run_id="run_conversation_change",
            event_type=EventType.FINAL_OUTPUT_PROPOSED,
            runtime_type="chat",
            payload={
                "content": change["draft_content"],
                "risk_context": template["incomplete_release_context"],
            },
        )
    )
    print_decision("conversation change becomes a draft risk preview", draft_decision)

    gateway = PublicationGateway(
        kernel,
        {"social_post": lambda **kwargs: {"published": True, "destination": kwargs["destination"]}},
        install_consequence_gate=False,
    )

    blocked = await gateway.call(
        PublicationRequest(
            name="social_post",
            content=change["draft_content"],
            destination="social",
            risk_context=RiskContext.from_dict(template["incomplete_release_context"]),
            idempotency_key="pub_incomplete_context",
        ),
        GatewayContext(run_id="run_conversation_change"),
    )
    print_gateway_result("incomplete context cannot publish", blocked)

    approvals = ApprovalManager()
    approval = approvals.create(
        "run_conversation_change",
        "evt_conversation_change_publication",
        reason={
            "requires_counter_evidence": True,
            "required_evidence": ["opened_artifacts", "approval_reason"],
        },
    )
    approved = approvals.approve(
        approval.id,
        {
            "opened_artifacts": True,
            "approval_reason": "reviewed generated risk hypotheses and alternate release context",
        },
    )
    print(f"\n== counter-evidence approval ==")
    print(f"  approval status: {approved.status.value}")
    print(f"  opened_artifacts: {approved.evidence['opened_artifacts']}")

    allowed = await gateway.call(
        PublicationRequest(
            name="social_post",
            content=change["draft_content"],
            destination="social",
            risk_context=RiskContext.from_dict(template["complete_release_context"]),
            risk_evidence=template["risk_evidence"],
            dry_run=True,
            idempotency_key="pub_complete_context",
        ),
        GatewayContext(run_id="run_conversation_change"),
    )
    print_gateway_result("completed context and evidence can dry-run", allowed)


if __name__ == "__main__":
    asyncio.run(main())
