"""
Django settings for nanodjango project
"""

from os import getenv
from pathlib import Path
from types import ModuleType

from nanodjango.app_meta import get_app_conf, get_app_module, get_templates

app_conf = get_app_conf()

# Find paths
ND_APP_MODULE: ModuleType = get_app_module()
if not ND_APP_MODULE or not ND_APP_MODULE.__file__:
    raise ValueError("Invalid app module - incorrect initialisation")
ND_FILEPATH: Path = Path(ND_APP_MODULE.__file__).absolute()
ND_APP_NAME: str = ND_FILEPATH.stem
BASE_DIR: Path = ND_FILEPATH.parent

MIGRATION_MODULES = {ND_APP_NAME: app_conf.get("MIGRATIONS_DIR", "migrations")}

# Standard Django settings
SECRET_KEY = getenv("DJANGO_SECRET_KEY", "not-a-secret")
DEBUG = True
ALLOWED_HOSTS = ["*"]
SITE_ID = 1

# Application definition
if app_conf.get("BARE"):
    # Minimal setup - no database required
    # Sessions and messages use cookie-based backends
    INSTALLED_APPS = [
        "django.contrib.sessions",
        "django.contrib.messages",
        "whitenoise.runserver_nostatic",
        "django.contrib.staticfiles",
    ]
    SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
    MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"
else:
    INSTALLED_APPS = app_conf.get(
        "INSTALLED_APPS",
        [
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "whitenoise.runserver_nostatic",
            "django.contrib.staticfiles",
        ],
    )
INSTALLED_APPS = INSTALLED_APPS + app_conf.get("EXTRA_APPS", [])

# Build middleware list based on installed apps
_middleware = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]
if "django.contrib.sessions" in INSTALLED_APPS:
    _middleware.append("django.contrib.sessions.middleware.SessionMiddleware")
_middleware.append("django.middleware.common.CommonMiddleware")
_middleware.append("django.middleware.csrf.CsrfViewMiddleware")
if "django.contrib.auth" in INSTALLED_APPS:
    _middleware.append("django.contrib.auth.middleware.AuthenticationMiddleware")
if "django.contrib.messages" in INSTALLED_APPS:
    _middleware.append("django.contrib.messages.middleware.MessageMiddleware")
_middleware.append("django.middleware.clickjacking.XFrameOptionsMiddleware")

MIDDLEWARE = _middleware

ROOT_URLCONF = "nanodjango.urls"

_context_processors = [
    "django.template.context_processors.debug",
    "django.template.context_processors.request",
]
if "django.contrib.auth" in INSTALLED_APPS:
    _context_processors.append("django.contrib.auth.context_processors.auth")
if "django.contrib.messages" in INSTALLED_APPS:
    _context_processors.append("django.contrib.messages.context_processors.messages")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(BASE_DIR / "templates")],
        "OPTIONS": {
            "context_processors": _context_processors,
            "loaders": [
                ("django.template.loaders.locmem.Loader", get_templates()),
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    }
]

WSGI_APPLICATION = "nanodjango.wsgi.application"

_sqlite_database = app_conf.get("SQLITE_DATABASE", ":memory:" if app_conf.get("BARE") else "db.sqlite3")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": _sqlite_database if _sqlite_database == ":memory:" else BASE_DIR / _sqlite_database,
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
_static_dir = BASE_DIR / "static"
STATICFILES_DIRS = [_static_dir] if _static_dir.is_dir() else []
STATIC_ROOT = BASE_DIR / "static-collected"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    # Django default:
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    # Whitenoise:
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# nanodjango specific config

# URL to serve admin site on
#
# If set, admin site will always be registered
#
# If not set, defaults to "/admin/" when the @app.admin decorator is used
ADMIN_URL = None

# URL to serve the API on, if @app.api is used
API_URL = "api/"

# Directory containing public files
PUBLIC_DIR = BASE_DIR / "public"
