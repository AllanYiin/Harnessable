from harnessable.capabilities import CapabilityProfile, CapabilitySelector, CapabilityType, PermissionChecker, PermissionContext
from harnessable import EnvSecretProvider, StaticSecretProvider
from harnessable.resilience import CircuitBreaker
from harnessable.tool_policy import ToolCapabilityProfile, build_tool_exposure_decision


def test_permission_default_deny_and_selector_boundary():
    source = CapabilityProfile(
        id="tool.primary",
        type=CapabilityType.TOOL,
        compatibility_class="search",
        permissions={"allowed_roles": ["assistant"]},
    )
    wider = CapabilityProfile(
        id="tool.wide",
        type=CapabilityType.TOOL,
        compatibility_class="search",
        permissions={"allowed_roles": ["*"]},
    )
    equivalent = CapabilityProfile(
        id="tool.equivalent",
        type=CapabilityType.TOOL,
        compatibility_class="search",
        permissions={"allowed_roles": ["assistant"]},
    )
    assert PermissionChecker().allowed(source, "guest") is False
    selected = CapabilitySelector().select([wider, equivalent], capability_type=CapabilityType.TOOL, compatibility_class="search", source=source)
    assert selected == [equivalent]


def test_circuit_breaker_opens_and_half_opens():
    breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=0)
    breaker.record_failure()
    assert breaker.allow_request() is True
    assert breaker.state.value == "HALF_OPEN"
    breaker.record_success()
    assert breaker.state.value == "HEALTHY"


def test_tool_access_policy_requires_tool_policy_for_power_tools():
    profiles = (
        ToolCapabilityProfile(name="standard.fs.grep", capability_class="read_only"),
        ToolCapabilityProfile(name="standard.code.container_exec", capability_class="code_execution", requires_tool_policy=True),
        ToolCapabilityProfile(name="harness.subagent.run", capability_class="delegation", requires_tool_policy=True),
    )

    restricted = build_tool_exposure_decision(
        tool_names=("standard.fs.grep", "standard.code.container_exec", "harness.subagent.run"),
        tool_policy_enabled=False,
        profiles=profiles,
    )
    full = build_tool_exposure_decision(
        tool_names=("standard.fs.grep", "standard.code.container_exec", "harness.subagent.run"),
        tool_policy_enabled=True,
        globally_excluded_tool_names=("harness.subagent.run",),
        profiles=profiles,
    )

    assert restricted.enabled_tool_names == ["standard.fs.grep"]
    assert restricted.denied_reasons["standard.code.container_exec"] == "tool_policy_required"
    assert full.enabled_tool_names == ["standard.fs.grep", "standard.code.container_exec"]
    assert full.denied_reasons["harness.subagent.run"] == "globally_excluded"


def test_permission_checker_supports_tenant_context_and_decisions():
    capability = CapabilityProfile(
        id="tool.tenant",
        type=CapabilityType.TOOL,
        permissions={"allowed_roles": ["assistant"], "allowed_tenant_ids": ["tenant_a"]},
    )
    checker = PermissionChecker()

    allowed = checker.decision(capability, PermissionContext(role="assistant", tenant_id="tenant_a"))
    denied = checker.decision(capability, PermissionContext(role="assistant", tenant_id="tenant_b"))

    assert allowed.allowed is True
    assert denied.allowed is False
    assert denied.reason == "tenant_not_allowed"


def test_secret_provider_seam_supports_static_and_env(monkeypatch):
    monkeypatch.setenv("HARNESSABLE_TOKEN", "env-secret")

    assert StaticSecretProvider({"token": "static-secret"}).get("token") == "static-secret"
    assert EnvSecretProvider(prefix="HARNESSABLE_").get("TOKEN") == "env-secret"


def test_permission_checker_supports_purpose_context():
    capability = CapabilityProfile(
        id="tool.purpose",
        type=CapabilityType.TOOL,
        permissions={"allowed_roles": ["assistant"], "allowed_purposes": ["debug"]},
    )

    assert PermissionChecker().decision(capability, PermissionContext(role="assistant", purpose="debug")).allowed is True
    assert PermissionChecker().decision(capability, PermissionContext(role="assistant", purpose="release")).reason == "purpose_not_allowed"
