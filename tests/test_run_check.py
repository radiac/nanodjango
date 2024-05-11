from .utils import cmd


def test_run_check__counter():
    result = cmd("examples/counter.py", "run", "check")
    assert result.stderr.strip() == ""
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."


def test_run_check__scale():
    result = cmd("examples/scale.py", "run", "check")
    assert result.stderr.strip() == ""
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."
