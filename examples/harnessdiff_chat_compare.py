from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

try:
    from _bootstrap import add_src_to_path
except ModuleNotFoundError:
    from examples._bootstrap import add_src_to_path

add_src_to_path()

from harnessable import HarnessKernel, HarnessProject
from harnessable.adapters import ChatRuntimeAdapter
from harnessable.decisions import RuntimeCommandType
from harnessable.gateways import GatewayContext, ModelRequest


SCHEMA_VERSION = "example.harnessdiff_chat_compare.v1"
PANES = ("NoHarness", "Harness")
DEFAULT_PROJECT_PATH = Path(__file__).parent / "projects" / "harnessdiff-chat-comparison"
TERMINAL_COMMANDS = {
    RuntimeCommandType.BLOCK,
    RuntimeCommandType.ABORT,
    RuntimeCommandType.FAIL_SAFE,
    RuntimeCommandType.REQUEST_APPROVAL,
}


async def run_comparison(
    prompt: str,
    *,
    project_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Run one prompt through a direct baseline and a Harness-controlled path."""
    project = HarnessProject.open(str(project_path or DEFAULT_PROJECT_PATH))
    kernel = HarnessKernel.from_project(project)
    adapter = ChatRuntimeAdapter(kernel)
    run_id = run_id or f"harnessdiff_{uuid4().hex[:12]}"
    output_root = Path(output_dir) if output_dir else project.path / "reports" / "harnessdiff-chat-comparison" / run_id
    output_root.mkdir(parents=True, exist_ok=True)

    no_harness = await _run_no_harness(prompt)
    harness = await _run_harness(prompt, run_id, project, kernel, adapter)

    panes = {
        "NoHarness": _persist_pane_result(project, output_root, "NoHarness", no_harness),
        "Harness": _persist_pane_result(project, output_root, "Harness", harness),
    }
    result = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "prompt": prompt,
        "panes": panes,
        "comparison": _build_comparison(panes),
        "artifact_root": str(output_root),
    }
    _write_json(output_root / "summary.json", result)
    return result


async def _run_no_harness(prompt: str) -> dict[str, Any]:
    chunks = _chunk_text(f"NoHarness direct response: {prompt}")
    return {
        "pane": "NoHarness",
        "prompt": prompt,
        "status": "completed",
        "chunks": chunks,
        "final_text": "".join(chunks),
        "events": [
            {"type": "delta", "sequence": sequence, "text": chunk}
            for sequence, chunk in enumerate(chunks)
        ]
        + [{"type": "completed", "sequence": len(chunks)}],
        "decisions": [],
        "runtime_command": None,
        "effect": None,
    }


async def _run_harness(
    prompt: str,
    run_id: str,
    project: HarnessProject,
    kernel: HarnessKernel,
    adapter: ChatRuntimeAdapter,
) -> dict[str, Any]:
    event = adapter.to_event(prompt, {"run_id": run_id})
    decision = kernel.emit(event)
    command = adapter.apply_decision(decision)
    chunks: list[str] = []
    status = "completed"

    if command.command_type in TERMINAL_COMMANDS:
        status = "blocked"
        chunks = [
            f"Harness stopped before model call: {command.command_type.value} "
            f"from {decision.rule_id or 'no-rule'}."
        ]
    else:
        context = GatewayContext(run_id=run_id, runtime_type="chat")
        async for chunk in adapter.model_gateway.call_stream(ModelRequest(prompt), context):
            chunks.append(chunk.text)

    records = project.state.read_events(run_id)
    decisions = [record["decision"] for record in records if "decision" in record]
    return {
        "pane": "Harness",
        "prompt": prompt,
        "status": status,
        "chunks": chunks,
        "final_text": "".join(chunks),
        "events": [record["event"] for record in records if "event" in record],
        "decisions": decisions,
        "runtime_command": command.command_type.value,
        "effect": decision.effect.value,
    }


def _persist_pane_result(
    project: HarnessProject,
    output_root: Path,
    pane: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    pane_dir = output_root / pane
    pane_dir.mkdir(parents=True, exist_ok=True)
    persisted = dict(result)
    artifact_ref = project.artifacts.create(
        {key: value for key, value in persisted.items() if key != "artifact_ref"},
        metadata={"example": "harnessdiff_chat_compare", "pane": pane},
    )
    persisted["artifact_ref"] = artifact_ref
    _write_json(pane_dir / "result.json", persisted)
    return persisted


def _build_comparison(panes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    no_harness = panes["NoHarness"]
    harness = panes["Harness"]
    return {
        "final_text_equal": no_harness["final_text"] == harness["final_text"],
        "output_character_delta": len(harness["final_text"]) - len(no_harness["final_text"]),
        "chunk_count_delta": len(harness["chunks"]) - len(no_harness["chunks"]),
        "harness_effect": harness["effect"],
        "harness_runtime_command": harness["runtime_command"],
        "harness_blocked": harness["runtime_command"]
        in {command.value for command in TERMINAL_COMMANDS},
    }


def _chunk_text(text: str, width: int = 12) -> list[str]:
    return [text[index : index + width] for index in range(0, len(text), width)] or [""]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def format_summary(result: dict[str, Any]) -> str:
    rows = [
        ("Pane", "Status", "Chunks", "Effect", "Command", "Artifact"),
        *[
            (
                pane,
                result["panes"][pane]["status"],
                str(len(result["panes"][pane]["chunks"])),
                str(result["panes"][pane]["effect"] or "-"),
                str(result["panes"][pane]["runtime_command"] or "-"),
                result["panes"][pane]["artifact_ref"],
            )
            for pane in PANES
        ],
    ]
    widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
    return "\n".join(
        "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))
        for row in rows
    )


async def _main_async() -> None:
    parser = argparse.ArgumentParser(
        description="Compare one prompt through NoHarness and Harness paths."
    )
    parser.add_argument("prompt", nargs="?", default="Summarize the value of runtime control planes.")
    parser.add_argument("--project", default=str(DEFAULT_PROJECT_PATH))
    parser.add_argument("--output-dir")
    parser.add_argument("--json", action="store_true", help="Print the full JSON result.")
    args = parser.parse_args()

    result = await run_comparison(
        args.prompt,
        project_path=args.project,
        output_dir=args.output_dir,
    )
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_summary(result))
        print(f"\nArtifacts: {result['artifact_root']}")


if __name__ == "__main__":
    asyncio.run(_main_async())
