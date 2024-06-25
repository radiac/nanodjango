"""
Django settings for nanodjango project
"""

from os import getenv
from pathlib import Path
from types import ModuleType

from nanodjango.app_meta import get_app_conf, get_app_module


app_conf = get_app_conf()

# Find paths
DF_APP_MODULE: ModuleType = get_app_module()
if not DF_APP_MODULE or not DF_APP_MODULE.__file__:
    raise ValueError("Invalid app module - incorrect initialisation")
DF_FILEPATH: Path = Path(DF_APP_MODULE.__file__).absolute()
DF_APP_NAME: str = DF_FILEPATH.stem
BASE_DIR: Path = DF_FILEPATH.parent

MIGRATION_MODULES = {DF_APP_NAME: app_conf.get("MIGRATIONS_DIR", "migrations")}

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
    "django.contrib.staticfiles",
] + app_conf.get("EXTRA_APPS", [])

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
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
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# nanodjango specific config
ADMIN_URL = None
API_URL = "api/"
