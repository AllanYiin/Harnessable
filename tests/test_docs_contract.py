from pathlib import Path


def test_stage_completion_and_docs_exist():
    required = [
        "docs/architecture.md",
        "docs/rules.md",
        "docs/fallback.md",
        "docs/gateways.md",
        "docs/adapters.md",
        "docs/project-persistence.md",
        "docs/cli.md",
        "docs/console.md",
        "docs/evals-and-replay.md",
        "docs/security.md",
        "docs/examples.md",
        "docs/artifact-review-policy.md",
        "docs/execution-evidence-policy.md",
        "docs/known-limitations.md",
        "docs/release-checklist.md",
        "docs/design-token-board.md",
        "docs/migration-harnessdiff-core-rules.md",
        "docs/test-matrix.md",
        "docs/stage-completion.md",
        "CHANGELOG.md",
    ]
    for path in required:
        assert Path(path).exists(), path
    matrix = Path("docs/stage-completion.md").read_text(encoding="utf-8")
    assert "Stage 14 | Complete" in matrix
