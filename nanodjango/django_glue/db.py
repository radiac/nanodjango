import os

from django.conf import settings
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.writer import MigrationWriter
from django.db.models.base import ModelBase


def patch_modelbase(app_name):
    """
    Because we don't have an app config and don't want to make users set an app label in
    their Meta, pretend they did it anyway
    """
    old_new = ModelBase.__new__

    def new_new(cls, name, bases, attrs, **kwargs):
        module = attrs["__module__"]
        if module in ("__main__", settings.ND_APP_MODULE.__name__):
            attrs["__module__"] = app_name
            attr_meta = attrs.get("Meta")
            if attr_meta:
                if not getattr(attr_meta, "app_label", None):
                    attr_meta.app_label = app_name
            else:

                class attr_meta:
                    app_label = app_name

                attrs["Meta"] = attr_meta

        return old_new(cls, name, bases, attrs, **kwargs)

    ModelBase.__new__ = new_new  # type: ignore


def patch_migrations(app_name):
    """
    Patch migrations to support missing migration dir
    """
    old_basedir = MigrationWriter.basedir.fget
    old_init = MigrationLoader.__init__

    def _migrations_path():
        # Convert dotted module path (e.g. "myapp.migrations") to a filesystem path
        # by stripping the app_name prefix, then resolve relative to BASE_DIR
        migration_module = settings.MIGRATION_MODULES.get(app_name, "migrations")
        if migration_module and migration_module.startswith(f"{app_name}."):
            migration_module = migration_module[len(f"{app_name}.") :]
        return settings.BASE_DIR / migration_module

    def new_basedir(self):
        if self.migration.app_label != app_name:
            return old_basedir(self)

        # Ensure migrations directory exists
        migrations_path = _migrations_path()
        migrations_path.mkdir(parents=True, exist_ok=True)
        return str(migrations_path)

    def new_init(self, connection, load=True, ignore_no_migrations=False):
        # Allow MigrationLoader to initialise if the init migration module is missing
        our_migration_module = settings.MIGRATION_MODULES.get(app_name, "migrations")
        migrations_dir = _migrations_path()

        has_migrations = migrations_dir.exists() and any(
            f.endswith(".py") and f != "__init__.py" for f in os.listdir(migrations_dir)
        )

        if not has_migrations:
            # Temporarily set our app's migrations to None so Django skips it
            settings.MIGRATION_MODULES[app_name] = None

        try:
            # Call original init
            old_init(self, connection, load, ignore_no_migrations)
        finally:
            # Restore original migration module setting if we changed it
            if not has_migrations:
                settings.MIGRATION_MODULES[app_name] = our_migration_module

    MigrationWriter.basedir = property(new_basedir)  # type: ignore
    MigrationLoader.__init__ = new_init


def patch_db(app_name):
    patch_modelbase(app_name)
    patch_migrations(app_name)
