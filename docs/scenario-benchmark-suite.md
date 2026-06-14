# Scenario Benchmark Suite

Stage 23 adds a small scenario and benchmark contract for policy rollout checks.

## Scenario Schema

`Scenario` contains:

- `scenario_id`
- `title`
- `source`
- `sensitivity`
- `steps`
- `limitations`

`ScenarioStep` maps to a `HarnessEvent` and can become an `EvalCase`. This lets
incident replay traces, synthetic stress cases, and policy-change cases share one
testable shape.

## Synthetic Generator

`ScenarioSimulator.generate_synthetic(seed, steps=N)` creates deterministic,
non-sensitive scenarios. The generator intentionally uses generic safe prompts
and records limitations because synthetic scenarios do not prove production
coverage.

## Trajectory Scoring

`TrajectoryScorer` computes a simple pass ratio over eval results. The scoring
hook is intentionally narrow so future benchmarks can replace or extend it
without changing the scenario schema.

`PolicyRolloutBenchmarker` produces a `PolicyRolloutBenchmarkReport` with:

- scenario count
- total and passed result counts
- trajectory score
- limitations

Reports explicitly warn when coverage is weak or only synthetic.

## Verification

```bash
python -m pytest tests/test_scenarios_benchmark.py tests/test_docs_contract.py
python -m compileall src
```
