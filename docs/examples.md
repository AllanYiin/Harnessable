# Examples

The builtins are sample baselines, not compliance guarantees.

Built-in rules:

- `security.pii.sample.v1`
- `security.prompt_injection.sample.v1`
- `governance.tool_permission.sample.v1`
- `quality.output_schema.sample.v1`
- `quality.citation_required.sample.v1`

Built-in fallback policies:

- `resilience.model.sample.v1`
- `resilience.tool.sample.v1`
- `resilience.side_effect_unknown.sample.v1`

Example projects:

- `examples/projects/chat-support`
- `examples/projects/agent-research`
- `examples/projects/multi-agent-review`

Run validation:

```bash
python -m pytest tests/test_builtin_examples.py
```
