from harnessable.capabilities import CapabilityProfile, CapabilitySelector, CapabilityType, PermissionChecker
from harnessable.resilience import CircuitBreaker


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
