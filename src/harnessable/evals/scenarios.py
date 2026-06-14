from __future__ import annotations

import random
import hashlib
from dataclasses import dataclass, field
from typing import Any

from harnessable.events import EventType, HarnessEvent

from .test_case import EvalCase


@dataclass(frozen=True)
class ScenarioStep:
    step_id: str
    event_type: str
    runtime_type: str = "chat"
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    expected_effect: str = "ALLOW"

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "event_type": self.event_type,
            "runtime_type": self.runtime_type,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
            "expected_effect": self.expected_effect,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ScenarioStep":
        return cls(**dict(payload))

    def to_event(self, scenario_id: str, run_id: str) -> HarnessEvent:
        return HarnessEvent(
            event_id=f"{scenario_id}:{self.step_id}",
            run_id=run_id,
            event_type=EventType(self.event_type),
            runtime_type=self.runtime_type,
            payload=dict(self.payload),
            metadata={**self.metadata, "scenario_id": scenario_id, "scenario_step_id": self.step_id},
        )


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    title: str
    source: str
    steps: tuple[ScenarioStep, ...]
    schema_version: str = "1"
    sensitivity: str = "synthetic_non_sensitive"
    limitations: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.scenario_id:
            raise ValueError("scenario_id is required")
        if not self.steps:
            raise ValueError("scenario must include at least one step")
        object.__setattr__(self, "steps", tuple(self.steps))
        object.__setattr__(self, "limitations", tuple(self.limitations))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scenario_id": self.scenario_id,
            "title": self.title,
            "source": self.source,
            "sensitivity": self.sensitivity,
            "steps": [step.to_dict() for step in self.steps],
            "limitations": list(self.limitations),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Scenario":
        data = dict(payload)
        data["steps"] = tuple(ScenarioStep.from_dict(step) for step in data.get("steps") or ())
        data["limitations"] = tuple(data.get("limitations") or ())
        return cls(**data)

    def to_eval_cases(self) -> list[EvalCase]:
        return [
            EvalCase(
                id=f"{self.scenario_id}:{step.step_id}",
                event=step.to_event(self.scenario_id, f"{self.scenario_id}:run").to_dict(),
                expected_effect=step.expected_effect,
                metadata={"scenario_id": self.scenario_id, "source": self.source, "sensitivity": self.sensitivity},
            )
            for step in self.steps
        ]


@dataclass(frozen=True)
class TrajectoryScore:
    total_steps: int
    passed_steps: int
    score: float
    limitations: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_steps": self.total_steps,
            "passed_steps": self.passed_steps,
            "score": self.score,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class PolicyRolloutBenchmarkReport:
    report_id: str
    schema_version: str
    scenario_count: int
    trajectory_score: TrajectoryScore
    result_summary: dict[str, Any]
    limitations: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "schema_version": self.schema_version,
            "scenario_count": self.scenario_count,
            "trajectory_score": self.trajectory_score.to_dict(),
            "result_summary": dict(self.result_summary),
            "limitations": list(self.limitations),
        }


class ScenarioSimulator:
    _EVENT_POOL = (
        EventType.USER_INPUT_RECEIVED.value,
        EventType.MODEL_CALL_REQUESTED.value,
        EventType.TOOL_CALL_REQUESTED.value,
        EventType.FINAL_OUTPUT_PROPOSED.value,
    )

    def generate_synthetic(self, seed: int | str, *, steps: int = 3) -> Scenario:
        rng = random.Random(str(seed))
        scenario_id = f"synthetic_{hashlib.sha256(str(seed).encode('utf-8')).hexdigest()[:12]}"
        generated_steps = []
        for index in range(steps):
            event_type = self._EVENT_POOL[rng.randrange(len(self._EVENT_POOL))]
            generated_steps.append(
                ScenarioStep(
                    step_id=f"step_{index + 1}",
                    event_type=event_type,
                    payload={"prompt": f"synthetic safe request {index + 1}", "sensitivity": "non_sensitive"},
                    metadata={"synthetic_seed": str(seed), "generator": "ScenarioSimulator"},
                )
            )
        return Scenario(
            scenario_id=scenario_id,
            title="Synthetic non-sensitive scenario",
            source="synthetic",
            steps=tuple(generated_steps),
            limitations=("synthetic scenario; does not represent production incidents",),
        )


class TrajectoryScorer:
    def score(self, results: list[dict[str, Any]]) -> TrajectoryScore:
        total = len(results)
        passed = sum(1 for result in results if result.get("passed") is True)
        limitations = []
        if total == 0:
            limitations.append("no trajectory results were provided")
        return TrajectoryScore(total_steps=total, passed_steps=passed, score=(passed / total if total else 0.0), limitations=tuple(limitations))


class PolicyRolloutBenchmarker:
    def build_report(self, scenarios: list[Scenario], results: list[dict[str, Any]]) -> PolicyRolloutBenchmarkReport:
        score = TrajectoryScorer().score(results)
        limitations = list(score.limitations)
        if len(scenarios) < 3:
            limitations.append("benchmark coverage is weak: fewer than three scenarios")
        if scenarios and all(scenario.source == "synthetic" for scenario in scenarios):
            limitations.append("benchmark uses only synthetic scenarios; include incident replay before rollout")
        return PolicyRolloutBenchmarkReport(
            report_id="policy_rollout_benchmark",
            schema_version="1",
            scenario_count=len(scenarios),
            trajectory_score=score,
            result_summary={"total_results": len(results), "passed_results": score.passed_steps},
            limitations=tuple(limitations),
        )
