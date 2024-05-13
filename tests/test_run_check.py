from .utils import cmd


def test_run_check__counter():
    result = cmd("run", "examples/counter.py", "check")
    assert result.stderr.strip() == ""
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."


def test_run_check__counter_app():
    result = cmd("run", "examples/counter.py:app", "check")
    assert result.stderr.strip() == ""
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."


def test_run_check__counter_module():
    result = cmd(
        "run", "counter:app", "check", cwd="examples", env={"PYTHONPATH": ".."}
    )
    assert result.stderr.strip() == ""
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."


def test_run_check__scale():
    result = cmd("run", "examples/scale.py", "check")
    assert result.stderr.strip() == ""
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."
