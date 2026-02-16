"""
Tests for Django.create_superuser
"""

import os
from unittest.mock import MagicMock, call, patch

import pytest


@pytest.fixture()
def no_users():
    """
    Mock get_user_model where no users exist
    """
    mock_user_model = MagicMock()
    mock_user_model.objects.filter.return_value.count.return_value = 0
    with patch("nanodjango.app.get_user_model", return_value=mock_user_model):
        yield


@pytest.fixture()
def has_user():
    """
    Mock get_user_model where user already exists
    """
    mock_user_model = MagicMock()
    mock_user_model.objects.filter.return_value.count.return_value = 1
    with patch("nanodjango.app.get_user_model", return_value=mock_user_model):
        yield


@pytest.fixture(autouse=True)
def clean_env():
    """
    Ensure DJANGO_SUPERUSER_PASSWORD is clean before each test and restore after
    """
    old = os.environ.pop("DJANGO_SUPERUSER_PASSWORD", None)
    yield
    if old is None:
        os.environ.pop("DJANGO_SUPERUSER_PASSWORD", None)
    else:
        os.environ["DJANGO_SUPERUSER_PASSWORD"] = old


@pytest.fixture()
def mock_exec():
    with patch("nanodjango.app.exec_manage") as mock:
        yield mock


@pytest.fixture()
def system_user():
    with patch("nanodjango.app.getpass") as mock_getpass:
        mock_getpass.getuser.return_value = "sysuser"
        yield


# nanodjango run script.py
# username=None, password=None → system user, random password, --no-input
def test_default__system_user_random_password(
    nanodjango_app, no_users, mock_exec, system_user, capsys
):
    nanodjango_app.create_superuser(None, None)

    mock_exec.assert_called_once_with(
        "createsuperuser", "--no-input", "--username", "sysuser", "--email", ""
    )
    assert os.environ.get("DJANGO_SUPERUSER_PASSWORD") is None
    out = capsys.readouterr().out
    assert "Created superuser" in out
    assert "Password:" in out


# nanodjango run --user script.py
# username="", password=None → interactive createsuperuser with random password in env
def test_user_flag_only__interactive_with_random_password(
    nanodjango_app, no_users, mock_exec, capsys
):
    nanodjango_app.create_superuser("", None)

    mock_exec.assert_called_once_with("createsuperuser")
    assert os.environ.get("DJANGO_SUPERUSER_PASSWORD") is None
    out = capsys.readouterr().out
    assert "Created superuser" in out
    assert "Password:" in out


# nanodjango run --user=bob script.py
# username="bob", password=None → --no-input --username bob, random password
def test_user_value__no_input_random_password(
    nanodjango_app, no_users, mock_exec, capsys
):
    nanodjango_app.create_superuser("bob", None)

    mock_exec.assert_called_once_with(
        "createsuperuser", "--no-input", "--username", "bob", "--email", ""
    )
    assert os.environ.get("DJANGO_SUPERUSER_PASSWORD") is None
    out = capsys.readouterr().out
    assert "Created superuser" in out
    assert "Password:" in out


# nanodjango run --pass script.py
# username=None, password="" → --no-input --username <system>, then changepassword
def test_pass_flag_only__no_input_then_changepassword(
    nanodjango_app, no_users, mock_exec, system_user
):
    nanodjango_app.create_superuser(None, "")

    assert mock_exec.call_args_list == [
        call("createsuperuser", "--no-input", "--username", "sysuser", "--email", ""),
        call("changepassword", "sysuser"),
    ]
    assert os.environ.get("DJANGO_SUPERUSER_PASSWORD") is None


# nanodjango run --pass=password script.py
# username=None, password="password" → --no-input --username <system>
def test_pass_value__no_input_with_password(
    nanodjango_app, no_users, mock_exec, system_user
):
    nanodjango_app.create_superuser(None, "mypass123")

    mock_exec.assert_called_once_with(
        "createsuperuser", "--no-input", "--username", "sysuser", "--email", ""
    )
    assert os.environ.get("DJANGO_SUPERUSER_PASSWORD") is None


# nanodjango run --user --pass script.py
# username="", password="" → fully interactive createsuperuser
def test_user_flag_pass_flag__fully_interactive(nanodjango_app, no_users, mock_exec):
    nanodjango_app.create_superuser("", "")

    mock_exec.assert_called_once_with("createsuperuser")
    assert os.environ.get("DJANGO_SUPERUSER_PASSWORD") is None


# nanodjango run --user --pass=password script.py
# username="", password="password" → interactive createsuperuser with password in env
def test_user_flag_pass_value__interactive_with_password(
    nanodjango_app, no_users, mock_exec
):
    nanodjango_app.create_superuser("", "mypass123")

    mock_exec.assert_called_once_with("createsuperuser")
    assert os.environ.get("DJANGO_SUPERUSER_PASSWORD") is None


# nanodjango run --user=bob --pass script.py
# username="bob", password="" → --no-input --username bob, then changepassword
def test_user_value_pass_flag__no_input_then_changepassword(
    nanodjango_app, no_users, mock_exec
):
    nanodjango_app.create_superuser("bob", "")

    assert mock_exec.call_args_list == [
        call("createsuperuser", "--no-input", "--username", "bob", "--email", ""),
        call("changepassword", "bob"),
    ]
    assert os.environ.get("DJANGO_SUPERUSER_PASSWORD") is None


# nanodjango run --user=bob --pass=password script.py
# username="bob", password="password" → --no-input --username bob
def test_user_value_pass_value__fully_non_interactive(
    nanodjango_app, no_users, mock_exec
):
    nanodjango_app.create_superuser("bob", "mypass123")

    mock_exec.assert_called_once_with(
        "createsuperuser", "--no-input", "--username", "bob", "--email", ""
    )
    assert os.environ.get("DJANGO_SUPERUSER_PASSWORD") is None


# DJANGO_SUPERUSER_PASSWORD set, no --pass → use env var, don't generate
def test_env_password__used_when_no_pass_flag(
    nanodjango_app, no_users, mock_exec, system_user, capsys
):
    os.environ["DJANGO_SUPERUSER_PASSWORD"] = "envpass"

    nanodjango_app.create_superuser(None, None)

    mock_exec.assert_called_once_with(
        "createsuperuser", "--no-input", "--username", "sysuser", "--email", ""
    )
    assert "Password:" not in capsys.readouterr().out


# DJANGO_SUPERUSER_PASSWORD set, --pass=override → use --pass value
def test_env_password__overridden_by_pass_value(
    nanodjango_app, no_users, mock_exec, system_user
):
    os.environ["DJANGO_SUPERUSER_PASSWORD"] = "envpass"

    nanodjango_app.create_superuser(None, "override")

    mock_exec.assert_called_once_with(
        "createsuperuser", "--no-input", "--username", "sysuser", "--email", ""
    )
    # Env var should be restored after the call
    assert os.environ.get("DJANGO_SUPERUSER_PASSWORD") == "envpass"


# User already exists → skip
def test_existing_user__skips(nanodjango_app, has_user, mock_exec, system_user, capsys):
    nanodjango_app.create_superuser(None, None)

    mock_exec.assert_not_called()
    assert "already exists" in capsys.readouterr().out


def test_existing_named_user__skips(nanodjango_app, has_user, mock_exec, capsys):
    nanodjango_app.create_superuser("bob", "mypass123")

    mock_exec.assert_not_called()
    assert "already exists" in capsys.readouterr().out
