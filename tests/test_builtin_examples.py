import json
from pathlib import Path

import yaml

from harnessable import HarnessKernel, HarnessProject
from harnessable.builtins import builtin_path
from harnessable.resilience import FallbackPolicy
from harnessable.rules import load_rule


def test_builtin_rules_load_and_parse():
    for file in builtin_path("rules").glob("*.yaml"):
        rule = load_rule(file)
        assert rule.id


def test_builtin_fallback_policies_parse():
    for file in builtin_path("fallback").glob("*.yaml"):
        policy = FallbackPolicy.from_dict(yaml.safe_load(file.read_text(encoding="utf-8")))
        assert policy.constraints


def test_example_projects_validate():
    for project_path in Path("examples/projects").iterdir():
        if not project_path.is_dir():
            continue
        project = HarnessProject.open(str(project_path))
        kernel = HarnessKernel.from_project(project)
        assert project.manifest.name
        assert kernel.rules.list()


def test_builtin_eval_json_parse():
    for file in builtin_path("evals").glob("*.json"):
        data = json.loads(file.read_text(encoding="utf-8"))
        assert data["id"]
        assert data["event"]["event_id"]
