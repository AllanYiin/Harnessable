import pytest

from harnessable import HarnessKernel, PluginManager
from harnessable.core import ValidationError
from harnessable.decisions import HarnessDecision
from harnessable.events import EventType, HarnessEvent
from harnessable.gateways import GatewayContext, ToolCallRequest, ToolGateway
from harnessable.rules.rule_loader import load_rule
from harnessable.validation import validate_payload


def test_import_validation_requires_schema_version_and_rejects_unknown_fields(tmp_path):
    bad = {
        "id": "rule.bad",
        "name": "Bad",
        "unexpected": True,
    }
    errors = validate_payload("rules", bad)
    assert "$: 'schema_version' is a required property" in errors
    assert "$: Additional properties are not allowed ('unexpected' was unexpected)" in errors

    source = tmp_path / "bad.yaml"
    source.write_text("id: rule.bad\nname: Bad\nunexpected: true\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_rule(source)


def test_plugin_hooks_wrap_emit_and_preserve_order():
    calls: list[str] = []

    class OrderedPlugin:
        name = "ordered"
        priority = 10

        def before_emit(self, event: HarnessEvent) -> HarnessEvent:
            calls.append("before_emit")
            event.metadata["plugin"] = "seen"
            return event

        def after_decision(self, event: HarnessEvent, decision: HarnessDecision) -> HarnessDecision:
            calls.append("after_decision")
            decision.telemetry["plugin"] = event.metadata["plugin"]
            return decision

        def before_gateway_call(self, request, context, capability):
            calls.append("before_gateway_call")
            return request

        def after_gateway_call(self, result, context, capability):
            calls.append("after_gateway_call")
            return result

        def on_error(self, event, exc) -> None:
            calls.append("on_error")

    manager = PluginManager()
    manager.register(OrderedPlugin())
    kernel = HarnessKernel(plugins=manager)
    decision = kernel.emit(HarnessEvent(event_id="evt", run_id="run", event_type=EventType.RUN_STARTED))

    assert calls == ["before_emit", "after_decision"]
    assert decision.telemetry["plugin"] == "seen"


@pytest.mark.asyncio
async def test_gateway_plugin_hooks_wrap_execution():
    calls: list[str] = []

    class GatewayPlugin:
        name = "gateway"
        priority = 10

        def before_emit(self, event: HarnessEvent) -> HarnessEvent:
            return event

        def after_decision(self, event: HarnessEvent, decision: HarnessDecision) -> HarnessDecision:
            return decision

        def before_gateway_call(self, request: ToolCallRequest, context, capability):
            calls.append("before_gateway_call")
            request.args["value"] = "mutated"
            return request

        def after_gateway_call(self, result, context, capability):
            calls.append("after_gateway_call")
            result.metadata["plugin"] = capability.id
            return result

        def on_error(self, event, exc) -> None:
            calls.append("on_error")

    manager = PluginManager()
    manager.register(GatewayPlugin())
    kernel = HarnessKernel(plugins=manager)
    gateway = ToolGateway(kernel, {"echo": lambda value: value})

    result = await gateway.call(ToolCallRequest("echo"), GatewayContext(run_id="run"))

    assert result.value.value == "mutated"
    assert result.metadata["plugin"] == "tool.local"
    assert calls == ["before_gateway_call", "after_gateway_call"]


def test_plugin_registration_rejects_partial_spi():
    class PartialPlugin:
        name = "partial"

    with pytest.raises(ValueError, match="missing hooks"):
        PluginManager().register(PartialPlugin())
