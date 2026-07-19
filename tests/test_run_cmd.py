"""Tests for run.cmd (PROJECT-GENESIS.md Tier 6 item 43: one-click run parity).

Static-content checks only - run.cmd is a Windows batch script and this suite runs
on Linux CI, so it asserts the script's shape rather than executing it. This app is
LIVE in production (Streamlit Cloud) - these tests also guard against run.cmd ever
touching .streamlit/ deploy config, since that config must never be edited outside
Zaid's explicit deploy workflow.
"""
from __future__ import annotations

from pathlib import Path

RUN_CMD = Path(__file__).resolve().parents[1] / "run.cmd"


def _text() -> str:
    return RUN_CMD.read_text(encoding="utf-8")


def test_run_cmd_exists():
    assert RUN_CMD.is_file()


def test_starts_the_app_matching_jarvis_config():
    text = _text()
    assert "PYTHONIOENCODING=utf-8" in text
    assert "venv\\Scripts\\python -m streamlit run app.py" in text


def test_opens_the_browser_on_the_app_port():
    assert "http://localhost:8501" in _text()


def test_never_touches_streamlit_deploy_config():
    """Only the executable lines matter here - REM comments may mention the deploy
    config by name to explain why it is untouched, without that counting as a hit."""
    executable_lines = "\n".join(
        line for line in _text().splitlines() if not line.strip().lower().startswith("rem")
    ).lower()
    assert ".streamlit" not in executable_lines
    assert "secrets.toml" not in executable_lines


def test_no_nested_quoting():
    """Mirrors the exact bug class jarvis-launcher's launcher rewrite fixed: a quote
    nested inside a quoted string makes cmd execute the literal, corrupted text."""
    for line in _text().splitlines():
        if "cmd /k" not in line:
            continue
        assert '\\"' not in line, f"escaped quote (nesting) found in: {line!r}"
        assert '""' not in line, f"doubled quote (nesting) found in: {line!r}"
        opens = line.count('"')
        assert opens % 2 == 0, f"unbalanced quotes in: {line!r}"
