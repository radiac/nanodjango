"""
Tests for BARE mode functionality
"""

import urllib.request

import pytest

from nanodjango.testing.utils import cmd, nanodjango_process, runserver

TEST_SCRIPT = "../examples/bare/bare.py"
TEST_BIND = "127.0.0.1:8043"


def test_bare_check():
    """BARE app passes Django system check"""
    result = cmd("manage", TEST_SCRIPT, "check")
    assert result.stderr.strip() == ""
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."


def test_bare_settings_installed_apps():
    """BARE mode has correct INSTALLED_APPS"""
    result = cmd(
        "manage", TEST_SCRIPT, "shell", "-c",
        "from django.conf import settings; print(list(settings.INSTALLED_APPS))"
    )
    apps = result.stdout.strip()
    # Should have sessions, messages, whitenoise, staticfiles
    assert "django.contrib.sessions" in apps
    assert "django.contrib.messages" in apps
    assert "whitenoise.runserver_nostatic" in apps
    assert "django.contrib.staticfiles" in apps
    # Should NOT have auth, admin, contenttypes
    assert "django.contrib.auth" not in apps
    assert "django.contrib.admin" not in apps
    assert "django.contrib.contenttypes" not in apps


def test_bare_settings_session_engine():
    """BARE mode uses signed_cookies session backend"""
    result = cmd(
        "manage", TEST_SCRIPT, "shell", "-c",
        "from django.conf import settings; print(settings.SESSION_ENGINE)"
    )
    assert "signed_cookies" in result.stdout


def test_bare_settings_message_storage():
    """BARE mode uses cookie message storage"""
    result = cmd(
        "manage", TEST_SCRIPT, "shell", "-c",
        "from django.conf import settings; print(settings.MESSAGE_STORAGE)"
    )
    assert "CookieStorage" in result.stdout


def test_bare_settings_memory_database():
    """BARE mode uses in-memory database by default"""
    result = cmd(
        "manage", TEST_SCRIPT, "shell", "-c",
        "from django.conf import settings; print(settings.DATABASES['default']['NAME'])"
    )
    assert ":memory:" in result.stdout


def test_bare_settings_staticfiles_dirs_empty():
    """STATICFILES_DIRS is empty when no static/ directory exists"""
    result = cmd(
        "manage", TEST_SCRIPT, "shell", "-c",
        "from django.conf import settings; print(settings.STATICFILES_DIRS)"
    )
    assert "[]" in result.stdout


@pytest.fixture(scope="module")
def bare_server():
    """Run the bare example server"""
    with (
        nanodjango_process("run", TEST_SCRIPT, TEST_BIND) as handle,
        runserver(handle),
    ):
        yield handle


def test_bare_index(bare_server):
    """BARE app can serve requests"""
    response = urllib.request.urlopen(f"http://{TEST_BIND}/", timeout=10)
    assert response.getcode() == 200
    content = response.read().decode("utf-8")
    assert "Visit count:" in content


def test_bare_sessions_work(bare_server):
    """Sessions work via cookies in BARE mode"""
    import http.cookiejar

    # Create a cookie jar to persist cookies between requests
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    # First request
    response1 = opener.open(f"http://{TEST_BIND}/", timeout=10)
    content1 = response1.read().decode("utf-8")
    assert "Visit count: 1" in content1

    # Second request with same cookies should increment
    response2 = opener.open(f"http://{TEST_BIND}/", timeout=10)
    content2 = response2.read().decode("utf-8")
    assert "Visit count: 2" in content2


def test_bare_messages_work(bare_server):
    """Messages work via cookies in BARE mode"""
    import http.cookiejar

    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    # Add a message
    response1 = opener.open(f"http://{TEST_BIND}/message/", timeout=10)
    assert response1.getcode() == 200

    # Retrieve messages
    response2 = opener.open(f"http://{TEST_BIND}/show-messages/", timeout=10)
    content = response2.read().decode("utf-8")
    assert "Hello from bare mode!" in content
