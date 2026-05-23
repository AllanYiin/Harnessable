from pathlib import Path

from harnessable.cli.main import main


def test_cli_init_validate_rules_preview_apply_and_fallback(tmp_path, capsys):
    project = tmp_path / "project"
    assert main(["init", str(project), "--name", "CLI"]) == 0
    assert main(["validate", str(project)]) == 0

    rule = tmp_path / "rule.yaml"
    rule.write_text("id: cli.rule\nname: CLI Rule\n", encoding="utf-8")
    assert main(["rules", "--project", str(project), "add", str(rule), "--preview"]) == 0
    preview_id = capsys.readouterr().out.strip().splitlines()[-1]
    assert not (project / "rules" / "rule.yaml").exists()
    assert main(["rules", "--project", str(project), "apply", preview_id]) == 0
    assert (project / "rules" / "rule.yaml").exists()
    assert main(["rules", "--project", str(project), "list"]) == 0

    fallback = project / "fallback" / "fb.yaml"
    fallback.write_text("id: fb\nname: FB\nconstraints:\n  max_total_attempts: 1\n", encoding="utf-8")
    assert main(["fallback", "--project", str(project), "validate"]) == 0
    assert main(["capabilities", "--project", str(project), "list"]) == 0


def test_console_static_contract():
    root = Path("src/harnessable/console/static")
    assert (root / "index.html").exists()
    css = (root / "styles.css").read_text(encoding="utf-8")
    html = (root / "index.html").read_text(encoding="utf-8")
    assert "aspect-ratio" in css
    assert "color-scheme: light" in css
    assert "Rule Import Review" in html
