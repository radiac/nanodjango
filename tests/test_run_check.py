from nanodjango.testing.utils import cmd


def test_run_check__counter():
    result = cmd("manage", "../examples/counter.py", "check")
    assert result.stderr.strip() == ""
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."


def test_run_check__counter_app():
    result = cmd("manage", "../examples/counter.py:app", "check")
    assert result.stderr.strip() == ""
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."


def test_run_check__counter_module():
    result = cmd("manage", "counter:app", "check", cwd="examples")
    assert result.stderr.strip() == ""
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."


def test_run_check__scale():
    result = cmd("manage", "../examples/scale/scale.py", "check")
    assert result.stderr.strip() == ""
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."


def test_staticfiles_dirs_when_exists():
    """STATICFILES_DIRS contains static/ when the directory exists"""
    result = cmd(
        "manage", "../examples/counter.py", "shell", "-c",
        "from django.conf import settings; print(settings.STATICFILES_DIRS)"
    )
    # examples/static exists, so it should be included
    assert "static" in result.stdout
    assert "[]" not in result.stdout
