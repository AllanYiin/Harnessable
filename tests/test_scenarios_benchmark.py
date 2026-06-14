from harnessable.evals import PolicyRolloutBenchmarker, Scenario, ScenarioSimulator, ScenarioStep, TrajectoryScorer


def test_scenario_schema_round_trips_to_eval_cases():
    scenario = Scenario(
        scenario_id="incident_1",
        title="Historical safe incident",
        source="incident_replay",
        steps=(
            ScenarioStep(
                step_id="step_1",
                event_type="USER_INPUT_RECEIVED",
                payload={"prompt": "safe request"},
                expected_effect="ALLOW",
            ),
        ),
    )

    restored = Scenario.from_dict(scenario.to_dict())
    cases = restored.to_eval_cases()

    assert restored.scenario_id == "incident_1"
    assert cases[0].id == "incident_1:step_1"
    assert cases[0].event["metadata"]["scenario_id"] == "incident_1"
    assert cases[0].expected_effect == "ALLOW"


def test_synthetic_scenario_generation_is_deterministic_and_non_sensitive():
    first = ScenarioSimulator().generate_synthetic("seed-a", steps=4)
    second = ScenarioSimulator().generate_synthetic("seed-a", steps=4)

    assert first.to_dict() == second.to_dict()
    assert first.sensitivity == "synthetic_non_sensitive"
    assert "secret" not in str(first.to_dict()).lower()
    assert first.limitations


def test_trajectory_scoring_and_benchmark_report_include_weak_coverage_limitations():
    results = [{"passed": True}, {"passed": False}]
    score = TrajectoryScorer().score(results)
    report = PolicyRolloutBenchmarker().build_report([ScenarioSimulator().generate_synthetic(7, steps=2)], results)

    assert score.total_steps == 2
    assert score.passed_steps == 1
    assert score.score == 0.5
    assert report.scenario_count == 1
    assert "fewer than three scenarios" in " ".join(report.limitations)
    assert "only synthetic scenarios" in " ".join(report.limitations)
