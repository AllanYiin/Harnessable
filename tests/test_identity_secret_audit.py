import json

from harnessable import AuditedSecretProvider, Principal, StaticSecretProvider
from harnessable.capabilities import CapabilityProfile, CapabilitySelector, CapabilityType, PermissionChecker, PermissionContext


def test_principal_permission_context_checks_project_and_authority():
    principal = Principal(
        principal_id="user_1",
        role="operator",
        tenant_id="tenant_a",
        project_memberships=("project_a",),
        approval_authorities=("publish_approval",),
    )
    capability = CapabilityProfile(
        id="action.publish",
        type=CapabilityType.EXTERNAL_ACTION,
        risk={"side_effect": True},
        permissions={
            "allowed_roles": ["operator"],
            "allowed_tenant_ids": ["tenant_a"],
            "allowed_purposes": ["release"],
            "allowed_project_ids": ["project_a"],
            "required_approval_authorities": ["publish_approval"],
        },
    )

    context = PermissionContext.from_principal(principal, purpose="release", project_id="project_a")
    assert PermissionChecker().decision(capability, context).allowed is True


def test_permission_checker_denies_wrong_tenant_purpose_project_and_authority():
    capability = CapabilityProfile(
        id="action.restricted",
        type=CapabilityType.EXTERNAL_ACTION,
        risk={"side_effect": True},
        permissions={
            "allowed_roles": ["operator"],
            "allowed_tenant_ids": ["tenant_a"],
            "allowed_purposes": ["release"],
            "allowed_project_ids": ["project_a"],
            "required_approval_authorities": ["publish_approval"],
        },
    )
    checker = PermissionChecker()

    assert checker.decision(capability, PermissionContext(role="operator", tenant_id="tenant_b", purpose="release")).reason == "tenant_not_allowed"
    assert checker.decision(capability, PermissionContext(role="operator", tenant_id="tenant_a", purpose="debug")).reason == "purpose_not_allowed"
    assert (
        checker.decision(
            capability,
            PermissionContext(role="operator", tenant_id="tenant_a", purpose="release", project_memberships=("project_b",)),
        ).reason
        == "project_membership_required"
    )
    assert (
        checker.decision(
            capability,
            PermissionContext(
                role="operator",
                tenant_id="tenant_a",
                purpose="release",
                project_memberships=("project_a",),
                approval_authorities=(),
            ),
        ).reason
        == "approval_authority_missing"
    )


def test_secret_access_audit_envelope_excludes_secret_value():
    provider = AuditedSecretProvider(StaticSecretProvider({"api_token": "very-secret"}), provider_id="static")
    principal = Principal(principal_id="user_1", role="operator", tenant_id="tenant_a")

    value = provider.get(
        "api_token",
        purpose="release",
        principal=principal,
        run_id="run_1",
        gateway_call_id="call_1",
        approved=True,
        audit_ref="audit_1",
    )

    assert value == "very-secret"
    record = provider.audit_log[0].to_dict()
    assert record["secret_ref"] == "api_token"
    assert record["principal_id"] == "user_1"
    assert record["approved"] is True
    assert "very-secret" not in json.dumps(record)


def test_fallback_selector_rejects_broader_project_and_authority_scope():
    source = CapabilityProfile(
        id="tool.source",
        type=CapabilityType.TOOL,
        compatibility_class="search",
        permissions={
            "allowed_roles": ["operator"],
            "allowed_project_ids": ["project_a"],
            "required_approval_authorities": ["restricted_search"],
        },
    )
    broader_project = CapabilityProfile(
        id="tool.broader_project",
        type=CapabilityType.TOOL,
        compatibility_class="search",
        permissions={"allowed_roles": ["operator"], "allowed_project_ids": ["project_b"]},
    )
    missing_authority = CapabilityProfile(
        id="tool.missing_authority",
        type=CapabilityType.TOOL,
        compatibility_class="search",
        permissions={"allowed_roles": ["operator"], "allowed_project_ids": ["project_a"]},
    )
    equivalent = CapabilityProfile(
        id="tool.equivalent",
        type=CapabilityType.TOOL,
        compatibility_class="search",
        permissions={
            "allowed_roles": ["operator"],
            "allowed_project_ids": ["project_a"],
            "required_approval_authorities": ["restricted_search"],
        },
    )

    selected = CapabilitySelector().select(
        [broader_project, missing_authority, equivalent],
        capability_type=CapabilityType.TOOL,
        compatibility_class="search",
        source=source,
    )

    assert selected == [equivalent]
