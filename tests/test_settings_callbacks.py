"""Tests for settings callback support (issue #74)"""

from nanodjango.testing.utils import run_app_code


def test_settings_callback_middleware():
    """Test that a callback can modify MIDDLEWARE"""
    result = run_app_code('''
from nanodjango import Django

app = Django(
    MIDDLEWARE=lambda m: ["test.FirstMiddleware"] + m + ["test.LastMiddleware"]
)

@app.route("/")
def index(request):
    return "Hello"

# Print the middleware to verify callback was applied
from django.conf import settings
print("MIDDLEWARE_FIRST:", settings.MIDDLEWARE[0])
print("MIDDLEWARE_LAST:", settings.MIDDLEWARE[-1])
''')

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "MIDDLEWARE_FIRST: test.FirstMiddleware" in result.stdout
    assert "MIDDLEWARE_LAST: test.LastMiddleware" in result.stdout


def test_settings_callback_installed_apps():
    """Test that a callback can filter INSTALLED_APPS"""
    result = run_app_code('''
from nanodjango import Django

# Use callback to remove admin from installed apps
app = Django(
    INSTALLED_APPS=lambda apps: [a for a in apps if "admin" not in a]
)

@app.route("/")
def index(request):
    return "Hello"

from django.conf import settings
print("HAS_ADMIN:", "django.contrib.admin" in settings.INSTALLED_APPS)
print("HAS_AUTH:", "django.contrib.auth" in settings.INSTALLED_APPS)
''')

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "HAS_ADMIN: False" in result.stdout  # Admin was removed by callback
    assert "HAS_AUTH: True" in result.stdout  # Other apps preserved


def test_settings_literal_callable_for_new_setting():
    """Test that callable values for NEW settings are kept as-is (not called)"""
    result = run_app_code('''
from nanodjango import Django

def my_header_func(headers, request, file):
    return headers

app = Django(
    WHITENOISE_ADD_HEADERS_FUNCTION=my_header_func
)

@app.route("/")
def index(request):
    return "Hello"

from django.conf import settings
# Should be the function itself, not the result of calling it
print("IS_CALLABLE:", callable(settings.WHITENOISE_ADD_HEADERS_FUNCTION))
print("FUNC_NAME:", settings.WHITENOISE_ADD_HEADERS_FUNCTION.__name__)
''')

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "IS_CALLABLE: True" in result.stdout
    assert "FUNC_NAME: my_header_func" in result.stdout


def test_settings_non_callable_unchanged():
    """Test that non-callable values still work normally"""
    result = run_app_code('''
from nanodjango import Django

app = Django(
    DEBUG=False,
    ALLOWED_HOSTS=["example.com", "localhost"]
)

@app.route("/")
def index(request):
    return "Hello"

from django.conf import settings
print("DEBUG:", settings.DEBUG)
print("HOSTS:", ",".join(settings.ALLOWED_HOSTS))
''')

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "DEBUG: False" in result.stdout
    assert "HOSTS: example.com,localhost" in result.stdout
