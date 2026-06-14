from pathlib import Path


def test_console_layout_contract():
    css = Path("src/harnessable/console/static/styles.css").read_text(encoding="utf-8")
    html = Path("src/harnessable/console/static/index.html").read_text(encoding="utf-8")
    assert "aspect-ratio: 16 / 7" in css
    assert "@media (max-width: 900px)" in css
    assert "aria-label=\"Fallback graph\"" in html
    assert "Operator Console" in html
    assert "Action Queue" in html
    assert "Decision Timeline" in html
    assert "Approval Evidence" in html
    assert "Replay Diff" in html
    assert "Artifact Registry" in html
    assert "data-action=\"export\"" in html
