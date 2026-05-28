import asyncio
from pathlib import Path
from typing import Any

try:
    from _bootstrap import add_src_to_path
except ModuleNotFoundError:
    from examples._bootstrap import add_src_to_path

add_src_to_path()

from harnessable import HarnessKernel
from harnessable.adapters import AgentRuntimeAdapter
from harnessable.gateways import ToolGateway
from harnessable.rules import load_rule


RULE_PATH = Path(__file__).parent / "projects" / "agent-research" / "rules" / "tool_permission.yaml"


def search_docs(query: str) -> dict[str, Any]:
    return {
        "query": query,
        "matches": [
            "Gateway is the boundary for external capabilities.",
            "Execution Governor turns HarnessDecision into RuntimeCommand.",
        ],
    }


def delete_index(name: str) -> str:
    raise AssertionError(f"dangerous tool should not execute: {name}")


def print_run_summary(kernel: HarnessKernel, decision_start: int, event_start: int, result: object) -> None:
    decisions = [record.payload for record in kernel.audit.by_kind("decision")[decision_start:]]
    events = kernel.events.events[event_start:]
    event_names = " -> ".join(event.event_type.value for event in events)
    decision_lines = []
    for event, decision in zip(events, decisions):
        effect = decision.get("effect")
        rule_id = decision.get("rule_id") or "default"
        decision_lines.append(f"{event.event_type.value}: {effect} via {rule_id}")

    print("  decisions:")
    for line in decision_lines:
        print(f"    - {line}")
    print(f"  events: {event_names}")
    if hasattr(result, "ok"):
        print(f"  gateway ok: {result.ok}")
        print(f"  gateway value: {result.value.value if result.ok else result.error}")
    else:
        print(f"  runtime command: {result.command_type.value}")


async def run_tool_case(adapter: AgentRuntimeAdapter, label: str, tool: str, args: dict[str, Any], run_id: str) -> None:
    kernel = adapter.kernel
    decision_start = len(kernel.audit.by_kind("decision"))
    event_start = len(kernel.events.events)
    result = await adapter.call_tool(tool, args, {"run_id": run_id})

    print(f"\n== {label} ==")
    print(f"  requested tool: {tool}")
    print(f"  args: {args}")
    print_run_summary(kernel, decision_start, event_start, result)


async def main() -> None:
    kernel = HarnessKernel()
    rule = load_rule(RULE_PATH)
    kernel.register_rule(rule)
    gateway = ToolGateway(kernel, {"search_docs": search_docs, "delete_index": delete_index})
    adapter = AgentRuntimeAdapter(kernel, gateway)

    print(f"Loaded rule: {rule.id}")
    await run_tool_case(
        adapter,
        "allowed read-only tool",
        "search_docs",
        {"query": "runtime control plane boundaries"},
        "run_agent_allowed",
    )
    await run_tool_case(
        adapter,
        "approval-gated dangerous tool",
        "delete_index",
        {"name": "production-index"},
        "run_agent_gated",
    )


if __name__ == "__main__":
    asyncio.run(main())
