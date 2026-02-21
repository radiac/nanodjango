"""Tests for nanodjango.conf module and settings configuration"""

from nanodjango.testing.utils import run_app_code

# =============================================================================
# Tests for backward compatibility with callable settings (from test_settings_callbacks.py)
# =============================================================================


def test_settings_callback_middleware():
    """Test that a callback can modify MIDDLEWARE"""
    result = run_app_code("""
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
print("HAS_LAST:", "test.LastMiddleware" in settings.MIDDLEWARE)
""")

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "MIDDLEWARE_FIRST: test.FirstMiddleware" in result.stdout
    assert "HAS_LAST: True" in result.stdout


def test_settings_callback_installed_apps():
    """Test that a callback can filter INSTALLED_APPS"""
    result = run_app_code("""
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
""")

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "HAS_ADMIN: False" in result.stdout  # Admin was removed by callback
    assert "HAS_AUTH: True" in result.stdout  # Other apps preserved


def test_settings_literal_callable_for_new_setting():
    """Test that callable values for NEW settings are kept as-is (not called)"""
    result = run_app_code("""
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
""")

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "IS_CALLABLE: True" in result.stdout
    assert "FUNC_NAME: my_header_func" in result.stdout


def test_settings_non_callable_unchanged():
    """Test that non-callable values still work normally"""
    result = run_app_code("""
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
""")

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "DEBUG: False" in result.stdout
    assert "HOSTS: example.com,localhost" in result.stdout


# =============================================================================
# Tests for new Django.conf modifiers
# =============================================================================


def test_conf_append_to_list():
    """Test Django.conf.append() to add items to a list setting"""
    result = run_app_code("""
from nanodjango import Django

app = Django(
    INSTALLED_APPS=Django.conf.append("django.contrib.sites", "django.contrib.sitemaps")
)

@app.route("/")
def index(request):
    return "Hello"

from django.conf import settings
print("HAS_SITES:", "django.contrib.sites" in settings.INSTALLED_APPS)
print("HAS_SITEMAPS:", "django.contrib.sitemaps" in settings.INSTALLED_APPS)
print("HAS_AUTH:", "django.contrib.auth" in settings.INSTALLED_APPS)
""")

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "HAS_SITES: True" in result.stdout
    assert "HAS_SITEMAPS: True" in result.stdout
    assert "HAS_AUTH: True" in result.stdout  # Original apps preserved


def test_conf_append_to_tuple():
    """Test Django.conf.append() converts tuples to lists"""
    result = run_app_code("""
from nanodjango import Django

app = Django(
    # MIDDLEWARE is often a tuple in Django
    MIDDLEWARE=Django.conf.append("test.MyMiddleware")
)

@app.route("/")
def index(request):
    return "Hello"

from django.conf import settings
print("HAS_MIDDLEWARE:", "test.MyMiddleware" in settings.MIDDLEWARE)
print("IS_LIST:", isinstance(settings.MIDDLEWARE, list))
""")

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "HAS_MIDDLEWARE: True" in result.stdout
    assert "IS_LIST: True" in result.stdout


def test_conf_remove_from_list():
    """Test Django.conf.remove() to remove items from a list"""
    result = run_app_code("""
from nanodjango import Django

app = Django(
    INSTALLED_APPS=Django.conf.remove("django.contrib.admin")
)

@app.route("/")
def index(request):
    return "Hello"

from django.conf import settings
print("HAS_ADMIN:", "django.contrib.admin" in settings.INSTALLED_APPS)
print("HAS_AUTH:", "django.contrib.auth" in settings.INSTALLED_APPS)
""")

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "HAS_ADMIN: False" in result.stdout
    assert "HAS_AUTH: True" in result.stdout


def test_conf_remove_from_dict():
    """Test Django.conf.remove() to remove keys from a dict"""
    result = run_app_code("""
from nanodjango import Django

app = Django(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    CACHES__default=Django.conf.remove("BACKEND")
)

@app.route("/")
def index(request):
    return "Hello"

from django.conf import settings
print("HAS_BACKEND:", "BACKEND" in settings.CACHES.get("default", {}))
""")

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "HAS_BACKEND: False" in result.stdout


def test_conf_env():
    """Test Django.conf.env() to get environment variables"""
    result = run_app_code("""
import os
from nanodjango import Django

os.environ["TEST_DEBUG"] = "true"

app = Django(
    SECRET_KEY=Django.conf.env("TEST_SECRET", "default-secret")
)

@app.route("/")
def index(request):
    return "Hello"

from django.conf import settings
print("SECRET:", settings.SECRET_KEY)
""")

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "SECRET: default-secret" in result.stdout


def test_conf_chaining():
    """Test chaining multiple Django.conf modifiers"""
    result = run_app_code("""
from nanodjango import Django

app = Django(
    INSTALLED_APPS=Django.conf(
        Django.conf.append("django.contrib.sites"),
        Django.conf.remove("django.contrib.admin"),
    )
)

@app.route("/")
def index(request):
    return "Hello"

from django.conf import settings
print("HAS_SITES:", "django.contrib.sites" in settings.INSTALLED_APPS)
print("HAS_ADMIN:", "django.contrib.admin" in settings.INSTALLED_APPS)
print("HAS_AUTH:", "django.contrib.auth" in settings.INSTALLED_APPS)
""")

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "HAS_SITES: True" in result.stdout
    assert "HAS_ADMIN: False" in result.stdout
    assert "HAS_AUTH: True" in result.stdout


def test_conf_nested_dict_modification():
    """Test Django.conf() for nested dict modifications"""
    result = run_app_code("""
from nanodjango import Django

app = Django(
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
    DATABASES__default__NAME="test.db"
)

@app.route("/")
def index(request):
    return "Hello"

from django.conf import settings
print("DB_NAME:", settings.DATABASES["default"]["NAME"])
""")

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "DB_NAME: test.db" in result.stdout


def test_conf_nested_list_modification():
    """Test Django.conf() for nested list modifications using _N syntax"""
    result = run_app_code("""
from nanodjango import Django

# Define a dummy context processor
def my_context_processor(request):
    return {}

app = Django(
    TEMPLATES__0__OPTIONS__context_processors=Django.conf.append(
        "__main__.my_context_processor"
    )
)

@app.route("/")
def index(request):
    return "Hello"

from django.conf import settings
processors = settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
print("HAS_CUSTOM:", "__main__.my_context_processor" in processors)
print("PROCESSOR_COUNT:", len(processors))
""")

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "HAS_CUSTOM: True" in result.stdout


def test_conf_modify_dict_key():
    """Test Django.conf() to modify specific dict keys"""
    result = run_app_code("""
from nanodjango import Django

app = Django(
    STORAGES=Django.conf(
        default={"BACKEND": "django.core.files.storage.FileSystemStorage"},
        staticfiles={"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}
    )
)

@app.route("/")
def index(request):
    return "Hello"

from django.conf import settings
print("HAS_DEFAULT:", "default" in settings.STORAGES)
print("HAS_STATICFILES:", "staticfiles" in settings.STORAGES)
""")

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "HAS_DEFAULT: True" in result.stdout
    assert "HAS_STATICFILES: True" in result.stdout


# =============================================================================
# Error handling tests
# =============================================================================


def test_conf_append_to_non_list():
    """Test that Django.conf.append() raises error on non-list"""
    result = run_app_code("""
from nanodjango import Django

app = Django(
    DEBUG=Django.conf.append("something")  # Can't append to bool
)

@app.route("/")
def index(request):
    return "Hello"
""")

    assert result.returncode != 0
    assert "ModifierError" in result.stderr or "append" in result.stderr.lower()


def test_conf_remove_from_non_list_or_dict():
    """Test that Django.conf.remove() raises error on invalid types"""
    result = run_app_code("""
from nanodjango import Django

app = Django(
    DEBUG=Django.conf.remove("something")  # Can't remove from bool
)

@app.route("/")
def index(request):
    return "Hello"
""")

    assert result.returncode != 0
    assert "ModifierError" in result.stderr or "remove" in result.stderr.lower()


def test_conf_error_path_tracking_simple():
    """Test that ModifierError includes the path in error messages"""
    result = run_app_code("""
from nanodjango import Django

app = Django(
    DEBUG=Django.conf.append("something")  # Can't append to bool
)

@app.route("/")
def index(request):
    return "Hello"
""")

    assert result.returncode != 0
    # Should show path like: DEBUG: Cannot append to...
    assert "DEBUG" in result.stderr


def test_conf_error_path_tracking_nested():
    """Test that ModifierError shows full path for nested errors"""
    result = run_app_code("""
from nanodjango import Django

app = Django(
    DATABASES__default__ENGINE=Django.conf.append("foo")  # Can't append to string
)

@app.route("/")
def index(request):
    return "Hello"
""")

    assert result.returncode != 0
    # Should show nested path like: DATABASES['default']['ENGINE']: Cannot append...
    assert "DATABASES" in result.stderr
    assert "default" in result.stderr
    assert "ENGINE" in result.stderr


def test_conf_error_path_tracking_list_index():
    """Test that ModifierError shows list indices in path"""
    result = run_app_code("""
from nanodjango import Django

app = Django(
    TEMPLATES__0__BACKEND=Django.conf.append("foo")  # Can't append to string
)

@app.route("/")
def index(request):
    return "Hello"
""")

    assert result.returncode != 0
    # Should show path like: TEMPLATES[0]['BACKEND']: Cannot append...
    assert "TEMPLATES" in result.stderr
    assert "0" in result.stderr or "[0]" in result.stderr
    assert "BACKEND" in result.stderr


def test_conf_context_processors_explicit_syntax():
    """Test adding context processor using explicit nested Django.conf() syntax"""
    result = run_app_code("""
from nanodjango import Django

# Define a dummy context processor
def my_context_processor(request):
    return {}

app = Django(
    TEMPLATES=Django.conf(
        _0=Django.conf(
            OPTIONS=Django.conf(
                context_processors=Django.conf.append(
                    "__main__.my_context_processor"
                )
            )
        )
    )
)

@app.route("/")
def index(request):
    return "Hello"

from django.conf import settings
processors = settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
print("HAS_CUSTOM:", "__main__.my_context_processor" in processors)
print("HAS_DEFAULT:", "django.template.context_processors.request" in processors)
""")

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "HAS_CUSTOM: True" in result.stdout
    assert "HAS_DEFAULT: True" in result.stdout  # Existing processors preserved
