from __future__ import annotations

from dataclasses import dataclass, field
from importlib.metadata import entry_points
from typing import Any, Protocol

from harnessable.decisions import HarnessDecision
from harnessable.events import HarnessEvent


class HarnessPlugin(Protocol):
    name: str
    priority: int

    def before_emit(self, event: HarnessEvent) -> HarnessEvent: ...

    def after_decision(self, event: HarnessEvent, decision: HarnessDecision) -> HarnessDecision: ...

    def before_gateway_call(self, request: Any, context: Any, capability: Any) -> Any: ...

    def after_gateway_call(self, result: Any, context: Any, capability: Any) -> Any: ...

    def on_error(self, event: HarnessEvent | None, exc: Exception) -> None: ...


@dataclass(slots=True)
class PluginManager:
    _plugins: list[HarnessPlugin] = field(default_factory=list)

    def register(self, plugin: HarnessPlugin) -> None:
        name = getattr(plugin, "name", None)
        if not name:
            raise ValueError("plugin name is required")
        if name in {item.name for item in self._plugins}:
            raise ValueError(f"duplicate plugin name: {name}")
        missing = [hook for hook in _REQUIRED_HOOKS if not callable(getattr(plugin, hook, None))]
        if missing:
            raise ValueError(f"plugin {name} missing hooks: {', '.join(missing)}")
        self._plugins.append(plugin)
        self._plugins.sort(key=lambda item: getattr(item, "priority", 100))

    def load_entry_points(self, group: str = "harnessable.plugins") -> None:
        for entry_point in entry_points().select(group=group):
            plugin_factory = entry_point.load()
            plugin = plugin_factory() if callable(plugin_factory) else plugin_factory
            self.register(plugin)

    @property
    def plugins(self) -> tuple[HarnessPlugin, ...]:
        return tuple(self._plugins)

    def run_before_emit(self, event: HarnessEvent) -> HarnessEvent:
        current = event
        for plugin in self._plugins:
            current = plugin.before_emit(current)
        return current

    def run_after_decision(self, event: HarnessEvent, decision: HarnessDecision) -> HarnessDecision:
        current = decision
        for plugin in self._plugins:
            current = plugin.after_decision(event, current)
        return current

    def run_before_gateway_call(self, request: Any, context: Any, capability: Any) -> Any:
        current = request
        for plugin in self._plugins:
            current = plugin.before_gateway_call(current, context, capability)
        return current

    def run_after_gateway_call(self, result: Any, context: Any, capability: Any) -> Any:
        current = result
        for plugin in self._plugins:
            current = plugin.after_gateway_call(current, context, capability)
        return current

    def fanout_error(self, event: HarnessEvent | None, exc: Exception) -> None:
        for plugin in self._plugins:
            try:
                plugin.on_error(event, exc)
            except Exception:
                continue


_REQUIRED_HOOKS = (
    "before_emit",
    "after_decision",
    "before_gateway_call",
    "after_gateway_call",
    "on_error",
)
