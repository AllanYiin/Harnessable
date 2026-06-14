# harnessable

`harnessable` is a Python package for building a provider-neutral LLM runtime control plane. It turns chat, agent, and multi-agent activity into a shared event model, evaluates rules, aggregates decisions, routes execution through gateways, records traces, and keeps fallback behavior policy-driven.

Core surfaces:

- Event Model: `HarnessEvent` standardizes runtime activity.
- Rule Engine: rules are registered, matched, evaluated, and converted into decisions.
- Decision Algebra: `HarnessDecision` effects have deterministic priority.
- Capability Gateway: model, tool, memory, resource, agent, and external action calls share one control lifecycle.
- State/Trace/Replay: projects, artifacts, traces, eval cases, and replay reports are local-file friendly.
- Fallback Plane: failure signals map to budgeted fallback plans without bypassing safety boundaries.
- Publishing Risk Harness: `ConsequenceGate` and `PublicationGateway` enforce release context, required scanner coverage, scanner findings, claim evidence, offer disclosure, provenance/similarity contracts, approval memory, and replayable incident learning without incident-specific blacklists.
- Code Execution Harness: `CodeExecutionHarness` and the `code_execution` capability contract describe sandbox backend, filesystem/network/resource policy, trust level, and enforcement gaps through the normal tool-call lifecycle. Harnessable does not depend on Docker, MXC, Node.js, or OS-specific sandbox SDKs.

## Quick start

```bash
python -m pip install -e .
pytest
python -m compileall src
harnessable init ./demo-project
harnessable validate ./demo-project
```

```python
from harnessable import HarnessKernel, HarnessProject
from harnessable.events import HarnessEvent, EventType

project = HarnessProject.create("./demo-project", "Demo")
kernel = HarnessKernel.from_project(project)

decision = kernel.emit(
    HarnessEvent(
        event_id="evt_1",
        run_id="run_1",
        event_type=EventType.USER_INPUT_RECEIVED,
        runtime_type="chat",
    )
)
print(decision.effect.value)
```

## Current scope

This repository implements the local SDK/CLI core and reference adapters. It does not connect to real LLM providers, remote databases, enterprise IAM, or hosted cloud services. Any future LLM-generated output must use a streaming interface. Imports are previewed before applying. UI graph containers must preserve aspect ratio.

## Documentation

- [Architecture](docs/architecture.md)
- [Rules](docs/rules.md)
- [Fallback](docs/fallback.md)
- [Gateways](docs/gateways.md)
- [Consequence Gate](docs/consequence-gate.md)
- [Adapters](docs/adapters.md)
- [Project persistence](docs/project-persistence.md)
- [CLI](docs/cli.md)
- [Console](docs/console.md)
- [Evals and replay](docs/evals-and-replay.md)
- [Security](docs/security.md)
- [Examples](docs/examples.md)
- [Runnable examples](examples/README.md)
- [Known limitations](docs/known-limitations.md)
- [Release checklist](docs/release-checklist.md)

## Example: NoHarness vs Harness

Run a lightweight HarnessDiff-style comparison without adding web app
dependencies:

```bash
python examples/harnessdiff_chat_compare.py "summarize runtime control planes"
```

The example compares a deterministic `NoHarness` baseline with a `Harness` path
that goes through `HarnessKernel`, `ChatRuntimeAdapter`, and
`ModelGateway.call_stream()`. It saves pane-separated JSON artifacts for replay
and inspection.

## Development commands

```bash
python -m pytest
python -m compileall src
python -m harnessable.cli.main init ./demo-project
python -m harnessable.cli.main validate ./demo-project
```

The project intentionally keeps dependencies small. Formatting and linting can be added without changing the runtime contracts.
