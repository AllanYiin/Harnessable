from pathlib import Path


def test_console_layout_contract():
    css = Path("src/harnessable/console/static/styles.css").read_text(encoding="utf-8")
    html = Path("src/harnessable/console/static/index.html").read_text(encoding="utf-8")
    assert "aspect-ratio: 16 / 7" in css
    assert "@media (max-width: 800px)" in css
    assert "aria-label=\"Fallback graph\"" in html
    assert "Rule Import Review" in html
