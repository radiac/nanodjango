from pathlib import Path

import pytest

from .utils import cmd


def test_run_check__counter():
    result = cmd("manage", "examples/counter.py", "check")
    assert result.stderr.strip() == ""
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."


def test_run_check__counter_app():
    result = cmd("manage", "examples/counter.py:app", "check")
    assert result.stderr.strip() == ""
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."


@pytest.fixture
def examples_path():
    return Path("examples")


def test_run_check__counter_module(examples_path: Path):
    result = cmd(
        "manage", "counter:app", "check", cwd=examples_path, env={"PYTHONPATH": ".."}
    )
    assert result.stderr.strip() == ""
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."


def test_run_check__scale():
    result = cmd("manage", "examples/scale/scale.py", "check")
    assert result.stderr.strip() == ""
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."
