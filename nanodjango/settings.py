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
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
] + app_conf.get("EXTRA_APPS", [])

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "nanodjango.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(BASE_DIR / "templates")],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "loaders": [
                ("django.template.loaders.locmem.Loader", get_templates()),
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    }
]

WSGI_APPLICATION = "nanodjango.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / app_conf.get("SQLITE_DATABASE", "db.sqlite3"),
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
