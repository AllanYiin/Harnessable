from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class StateStore:
    def __init__(self, project_path: str | Path) -> None:
        self.runs = Path(project_path) / "runs"
        self.runs.mkdir(parents=True, exist_ok=True)

    def append_event(self, run_id: str, record: dict[str, Any]) -> None:
        path = self.runs / f"{run_id}.jsonl"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    def read_events(self, run_id: str) -> list[dict[str, Any]]:
        path = self.runs / f"{run_id}.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
