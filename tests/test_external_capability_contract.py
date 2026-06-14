import pytest

from harnessable import HarnessKernel
from harnessable.capabilities import (
    CapabilityType,
    ExternalCapabilityContract,
    contract_from_capability,
    normalize_a2a_contract,
    normalize_function_contract,
    normalize_mcp_contract,
    same_or_stricter_contract,
)
from harnessable.gateways import GatewayContext, ToolCallRequest, ToolGateway


def test_external_contract_round_trips_and_maps_to_capability_profile():
    contract = normalize_function_contract(
        "tool.search",
        input_schema={"type": "object", "properties": {"q": {"type": "string"}}},
        risk_labels=["network"],
        approval_route={"required": True, "route": "security"},
        tenant_constraints={"allowed_tenant_ids": ["tenant_a"]},
        purpose_constraints={"allowed_purposes": ["research"]},
        data_access_scope={"data_classification": "internal"},
        side_effect_profile={"side_effect": False, "destructive_potential": "none"},
        cost_budget={"max_call_cost_usd": 0.01},
    )

    restored = ExternalCapabilityContract.from_dict(contract.to_dict())
    profile = restored.to_capability_profile()

    assert profile.type == CapabilityType.TOOL
    assert profile.contracts["external_capability"]["protocol"] == "function"
    assert profile.risk["risk_labels"] == ["network"]
    assert profile.permissions["allowed_tenant_ids"] == ["tenant_a"]
    assert profile.approval["required"] is True
    assert contract_from_capability(profile).capability_id == "tool.search"


def test_mcp_and_a2a_normalizers_do_not_require_runtime_dependencies():
    mcp = normalize_mcp_contract(
        {"name": "mcp.search", "inputSchema": {"type": "object"}},
        tenant_constraints={"allowed_tenant_ids": ["tenant_a"]},
        purpose_constraints={"allowed_purposes": ["support"]},
    )
    a2a = normalize_a2a_contract(
        {"name": "agent.reviewer", "capabilities": {"streaming": True}, "security": {"schemes": ["bearer"]}},
        tenant_constraints={"allowed_tenant_ids": ["tenant_a"]},
        purpose_constraints={"allowed_purposes": ["review"]},
    )

    assert mcp.protocol == "mcp"
    assert a2a.protocol == "a2a"
    assert mcp.descriptor_hash
    assert a2a.input_schema_hash


def test_contract_warnings_surface_missing_high_risk_metadata():
    contract = ExternalCapabilityContract(capability_id="mcp.high_risk", protocol="mcp", risk_labels=["external_network"])

    assert "missing_descriptor_hash" in contract.warnings
    assert "missing_input_schema_hash" in contract.warnings
    assert "missing_output_schema_hash" in contract.warnings
    assert "missing_approval_route" in contract.warnings
    assert "missing_tenant_constraints" in contract.warnings


def test_fallback_contract_cannot_broaden_tenant_risk_or_approval_boundary():
    source = normalize_function_contract(
        "tool.source",
        tenant_constraints={"allowed_tenant_ids": ["tenant_a"]},
        purpose_constraints={"allowed_purposes": ["research"]},
        approval_route={"required": True},
        data_access_scope={"data_classification": "confidential"},
        risk={"network_scope": "allowlisted", "exfiltration_risk": "medium"},
        side_effect_profile={"destructive_potential": "reversible"},
        cost_budget={"max_call_cost_usd": 0.02},
    )
    broader = normalize_function_contract(
        "tool.broader",
        tenant_constraints={"allowed_tenant_ids": ["tenant_a", "tenant_b"]},
        purpose_constraints={"allowed_purposes": ["research"]},
        approval_route={"required": True},
        data_access_scope={"data_classification": "secret"},
        risk={"network_scope": "internet", "exfiltration_risk": "high"},
        side_effect_profile={"destructive_potential": "irreversible"},
        cost_budget={"max_call_cost_usd": 0.03},
    )
    stricter = normalize_function_contract(
        "tool.strict",
        tenant_constraints={"allowed_tenant_ids": ["tenant_a"]},
        purpose_constraints={"allowed_purposes": ["research"]},
        approval_route={"required": True},
        data_access_scope={"data_classification": "internal"},
        risk={"network_scope": "none", "exfiltration_risk": "low"},
        side_effect_profile={"destructive_potential": "none"},
        cost_budget={"max_call_cost_usd": 0.01},
    )

    assert same_or_stricter_contract(source, broader) is False
    assert same_or_stricter_contract(source, stricter) is True


@pytest.mark.asyncio
async def test_gateway_event_exposes_external_contract_metadata():
    kernel = HarnessKernel()
    contract = normalize_function_contract(
        "tool.echo",
        tenant_constraints={"allowed_tenant_ids": ["tenant_a"]},
        purpose_constraints={"allowed_purposes": ["support"]},
    )
    gateway = ToolGateway(kernel, {"echo": lambda value: value}, capability=contract.to_capability_profile())

    result = await gateway.call(ToolCallRequest("echo", {"value": "ok"}), GatewayContext(run_id="run_contract"))

    assert result.ok is True
    event = kernel.traces.by_kind("event")[0].payload
    assert event["capability"]["contracts"]["external_capability"]["protocol"] == "function"
    assert event["metadata"]["external_capability_contract"]["capability_id"] == "tool.echo"

