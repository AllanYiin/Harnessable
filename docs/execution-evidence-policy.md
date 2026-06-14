# Execution Evidence Policy

Execution evidence policy prevents a runtime from presenting generated code,
HTML, tests, builds, or implementation changes as verified unless a code
execution capability actually ran or the runtime explicitly reports that it
could not run.

## Boundary

Harnessable owns the runtime-neutral decision:

- detect tasks that require executable evidence;
- emit a versioned `ExecutionEvidenceRequirement`;
- identify the required capability class as `code_execution`;
- preserve adapter-specific tool names as optional metadata.

HarnessDiff owns the adapter mapping:

- decide whether the Harness profile has `tool_policy` enabled;
- decide whether `standard.code.container_exec` is available;
- map the core `code_execution` capability class to that tool name;
- append provider instructions and preserve run evidence.

Harnessable must not depend on Docker, OpenAI Responses, MXC, Node.js, or a
specific command runner.

## Core API

```python
from harnessable.tool_policy import build_execution_evidence_requirement

requirement = build_execution_evidence_requirement(
    task_text="Fix the React component and run tests",
    enabled=True,
    code_execution_available=True,
    required_tool_names=["standard.code.container_exec"],
    surface="chat",
)
```

The returned `ExecutionEvidenceRequirement.to_dict()` includes:

- `schema_version`
- `requires_execution_evidence`
- `required_capability_classes`
- `required_tool_names`
- `reason`
- `surface`

`required_tool_names` is optional adapter data. A runtime that does not expose
HarnessDiff's `standard.code.container_exec` should still use
`required_capability_classes=["code_execution"]`.

## Compatibility

Existing HarnessDiff callers can keep using:

- `build_code_execution_policy(...)`
- `requires_code_execution_evidence(...)`
- `execution_policy_task_text(...)`
- `apply_execution_policy_instructions(...)`

Those functions should be wrappers around Harnessable core. They should not
maintain their own coding-task term lists.

## Verification

Harnessable coverage:

```powershell
python -m pytest tests/test_execution_evidence_policy.py
```

HarnessDiff adapter coverage:

```powershell
python -m pytest tests/api/test_execution_policy.py
```
