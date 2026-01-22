"""
Early Django configuration via AST extraction.

This module configures Django during `from nanodjango import Django` by:
1. Injecting defaults (BASE_DIR, INSTALLED_APPS, etc.) into the importing module
2. AST-parsing the source file to find user setting overrides
3. Executing those settings with injected context
4. Merging defaults + overrides and calling django.setup()

This allows Django imports to work in PEP8-compliant order.
"""

from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path
from typing import Any

from . import app_meta


class EarlyConfigurator:
    """
    Handles early Django configuration by extracting settings from
    the importing module's source before it finishes executing.
    """

    _configured: bool = False
    _source_file: Path | None = None
    _app_name: str | None = None
    _base_dir: Path | None = None
    _injected_defaults: dict[str, Any] = {}
    _user_overrides: dict[str, Any] = {}
    _final_settings: dict[str, Any] = {}

    @classmethod
    def get_defaults(cls, base_dir: Path, app_name: str) -> dict[str, Any]:
        """
        Return complete Django settings defaults.

        These are injected into the importing module's namespace so:
        - Users can reference them (e.g., STATIC_ROOT = BASE_DIR / "static")
        - The file becomes a complete Django settings module
        """
        return {
            # Utilities for user convenience
            "BASE_DIR": base_dir,
            "Path": Path,

            # Core Django settings
            "DEBUG": True,
            "SECRET_KEY": "nanodjango-dev-key-override-in-production",
            "ALLOWED_HOSTS": ["*"],
            "ROOT_URLCONF": "nanodjango.urls",
            "WSGI_APPLICATION": "nanodjango.wsgi.application",
            "DEFAULT_AUTO_FIELD": "django.db.models.BigAutoField",
            "SITE_ID": 1,

            "INSTALLED_APPS": [
                "django.contrib.admin",
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "django.contrib.sessions",
                "django.contrib.messages",
                "whitenoise.runserver_nostatic",
                "django.contrib.staticfiles",
            ],

            "MIDDLEWARE": [
                "django.middleware.security.SecurityMiddleware",
                "whitenoise.middleware.WhiteNoiseMiddleware",
                "django.contrib.sessions.middleware.SessionMiddleware",
                "django.middleware.common.CommonMiddleware",
                "django.middleware.csrf.CsrfViewMiddleware",
                "django.contrib.auth.middleware.AuthenticationMiddleware",
                "django.contrib.messages.middleware.MessageMiddleware",
                "django.middleware.clickjacking.XFrameOptionsMiddleware",
            ],

            "TEMPLATES": [
                {
                    "BACKEND": "django.template.backends.django.DjangoTemplates",
                    "DIRS": [base_dir / "templates"],
                    "OPTIONS": {
                        "context_processors": [
                            "django.template.context_processors.debug",
                            "django.template.context_processors.request",
                            "django.contrib.auth.context_processors.auth",
                            "django.contrib.messages.context_processors.messages",
                        ],
                        "loaders": [
                            # locmem.Loader enables in-memory templates (app.templates)
                            ("django.template.loaders.locmem.Loader", app_meta.get_templates()),
                            "django.template.loaders.filesystem.Loader",
                            "django.template.loaders.app_directories.Loader",
                        ],
                    },
                }
            ],

            "DATABASES": {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": base_dir / "db.sqlite3",
                }
            },

            "AUTH_PASSWORD_VALIDATORS": [
                {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
                {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
                {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
                {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
            ],

            "LANGUAGE_CODE": "en-us",
            "TIME_ZONE": "UTC",
            "USE_I18N": True,
            "USE_TZ": True,

            "STATIC_URL": "/static/",
            "STATICFILES_DIRS": [base_dir / "static"],
            "STATIC_ROOT": base_dir / "static-collected",

            "MEDIA_URL": "/media/",
            "MEDIA_ROOT": base_dir / "media",

            "STORAGES": {
                "default": {
                    "BACKEND": "django.core.files.storage.FileSystemStorage",
                },
                "staticfiles": {
                    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
                },
            },

            # nanodjango specific
            "ADMIN_URL": None,
            "API_URL": "api/",
            "PUBLIC_DIR": base_dir / "public",
            "SQLITE_DATABASE": "db.sqlite3",
            "MIGRATIONS_DIR": "migrations",
        }

    @classmethod
    def extract_settings_from_source(
        cls,
        source: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        AST-parse source and execute uppercase assignments to extract settings.

        The context contains injected defaults so expressions like
        `BASE_DIR / "static"` can be evaluated.
        """
        tree = ast.parse(source)

        # Build execution context
        exec_context = context.copy()
        exec_context["os"] = __import__("os")
        exec_context["__builtins__"] = __builtins__

        settings: dict[str, Any] = {}

        for node in ast.iter_child_nodes(tree):
            # Simple assignment: DEBUG = True
            if isinstance(node, ast.Assign):
                names = [
                    t.id for t in node.targets
                    if isinstance(t, ast.Name) and t.id.isupper()
                ]
                if names:
                    try:
                        mod = ast.Module(body=[node], type_ignores=[])
                        code = compile(mod, "<settings>", "exec")
                        exec(code, exec_context)
                        for name in names:
                            if name in exec_context:
                                settings[name] = exec_context[name]
                    except Exception:
                        # Skip settings that can't be evaluated
                        pass

            # Annotated assignment: DEBUG: bool = True
            elif isinstance(node, ast.AnnAssign):
                if (
                    isinstance(node.target, ast.Name)
                    and node.target.id.isupper()
                    and node.value
                ):
                    name = node.target.id
                    try:
                        mod = ast.Module(body=[node], type_ignores=[])
                        code = compile(mod, "<settings>", "exec")
                        exec(code, exec_context)
                        if name in exec_context:
                            settings[name] = exec_context[name]
                    except Exception:
                        pass

            # Augmented assignment: INSTALLED_APPS += ["myapp"]
            elif isinstance(node, ast.AugAssign):
                if isinstance(node.target, ast.Name) and node.target.id.isupper():
                    name = node.target.id
                    try:
                        mod = ast.Module(body=[node], type_ignores=[])
                        code = compile(mod, "<settings>", "exec")
                        exec(code, exec_context)
                        if name in exec_context:
                            settings[name] = exec_context[name]
                    except Exception:
                        pass

        return settings

    @classmethod
    def find_importing_module(cls) -> tuple[dict[str, Any] | None, str | None]:
        """
        Walk up the stack to find the module that's importing nanodjango.

        Returns (caller_globals, caller_file) or (None, None) if not found.
        """
        # Get the nanodjango package directory to skip internal modules
        nanodjango_pkg_dir = Path(__file__).parent

        for frame_info in inspect.stack():
            filename = frame_info.filename

            # Skip nanodjango package internals (but not examples, tests, etc.)
            try:
                filepath = Path(filename).resolve()
                if filepath.is_relative_to(nanodjango_pkg_dir):
                    continue
            except (ValueError, OSError):
                pass

            # Skip importlib internals
            if "importlib" in filename:
                continue

            # Skip frozen/built-in modules
            if filename.startswith("<"):
                continue

            filepath = Path(filename)
            if filepath.exists() and filepath.suffix == ".py":
                return frame_info.frame.f_globals, filename

        return None, None

    @classmethod
    def configure(cls) -> bool:
        """
        Configure Django early by extracting settings from the importing module.

        This is called during `from nanodjango import Django`.

        Returns True if early configuration was performed, False otherwise.
        """
        if cls._configured:
            return False

        # Find the module that's importing Django
        # With lazy loading, this works in both direct mode and CLI mode
        caller_globals, caller_file = cls.find_importing_module()

        if not caller_globals or not caller_file:
            return False

        source_path = Path(caller_file).resolve()

        # Don't early-configure for nanodjango package internals
        nanodjango_pkg_dir = Path(__file__).parent
        try:
            if source_path.is_relative_to(nanodjango_pkg_dir):
                return False
        except (ValueError, OSError):
            pass

        cls._source_file = source_path
        cls._base_dir = source_path.parent
        cls._app_name = source_path.stem

        # Set app_meta so it's available for models etc.
        caller_module_name = caller_globals.get("__name__", cls._app_name)
        if caller_module_name in sys.modules:
            app_meta._app_module = sys.modules[caller_module_name]

            # Also register the module under its file stem name
            # This prevents Django's autodiscover from re-importing the script
            if caller_module_name != cls._app_name and cls._app_name not in sys.modules:
                sys.modules[cls._app_name] = sys.modules[caller_module_name]

        # Step 1: Get defaults
        defaults = cls.get_defaults(cls._base_dir, cls._app_name)
        cls._injected_defaults = defaults.copy()

        # Step 2: Inject defaults into caller's namespace
        for name, value in defaults.items():
            if name not in caller_globals:
                caller_globals[name] = value

        # Step 3: Read source and extract user overrides
        try:
            source = source_path.read_text()
            overrides = cls.extract_settings_from_source(source, defaults)
            cls._user_overrides = overrides
        except Exception:
            overrides = {}

        # Step 4: Merge (user overrides take precedence)
        final = {**defaults, **overrides}
        cls._final_settings = final

        # Step 5: Configure Django
        # Filter to Django settings only (uppercase, not utilities)
        django_settings = {
            k: v for k, v in final.items()
            if k.isupper() and k not in ("Path",) and not k.startswith("_")
        }

        # Set MIGRATION_MODULES based on MIGRATIONS_DIR
        migrations_dir = final.get("MIGRATIONS_DIR", "migrations")
        django_settings["MIGRATION_MODULES"] = {cls._app_name: migrations_dir}

        try:
            import django
            from django.conf import settings as django_settings_obj

            if not django_settings_obj.configured:
                django_settings_obj.configure(**django_settings)

                # Register the app with Django's app registry BEFORE setup()
                # This prevents Django from trying to re-import the module
                cls._register_app(
                    cls._app_name,
                    app_meta._app_module,
                    cls._source_file,
                )

                django.setup()

                # Patch ModelBase so models defined in __main__ get proper app_label
                from .django_glue.db import patch_modelbase
                patch_modelbase(cls._app_name)

                cls._configured = True
                return True
        except Exception:
            # If early config fails, fall back to normal initialization
            pass

        return False

    @classmethod
    def _register_app(
        cls,
        app_name: str,
        app_module: Any,
        source_file: Path,
    ) -> None:
        """
        Register the app with Django's app registry before setup().

        This is similar to what django_glue.apps.prepare_apps does, but
        without depending on the settings module.
        """
        from django.apps.config import AppConfig
        from django.apps.registry import apps as apps_registry

        # Create a custom AppConfig with hardcoded path
        class EarlyAppConfig(AppConfig):
            path = str(source_file.parent)

        app_config = EarlyAppConfig(app_name=app_name, app_module=app_module)
        apps_registry.app_configs[app_config.label] = app_config
        app_config.apps = apps_registry
        app_config.models = {}

    @classmethod
    def is_configured(cls) -> bool:
        """Check if early configuration was performed."""
        return cls._configured

    @classmethod
    def get_app_info(cls) -> tuple[Path | None, str | None, Path | None]:
        """Return (source_file, app_name, base_dir) from early config."""
        return cls._source_file, cls._app_name, cls._base_dir

    @classmethod
    def get_settings(cls) -> dict[str, Any]:
        """Return the final merged settings."""
        return cls._final_settings.copy()

    @classmethod
    def get_user_overrides(cls) -> dict[str, Any]:
        """Return settings that were overridden by the user."""
        return cls._user_overrides.copy()

    @classmethod
    def reset(cls) -> None:
        """Reset state (primarily for testing)."""
        cls._configured = False
        cls._source_file = None
        cls._app_name = None
        cls._base_dir = None
        cls._injected_defaults = {}
        cls._user_overrides = {}
        cls._final_settings = {}


def configure_early() -> bool:
    """
    Attempt early Django configuration.

    Called automatically when nanodjango is imported.
    """
    return EarlyConfigurator.configure()
