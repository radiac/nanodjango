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
        if module == "__main__":
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
    Migrations needs a root path
    """
    old_basedir = MigrationWriter.basedir.fget
    old_load_disk = MigrationLoader.load_disk

    def new_basedir(self):
        if self.migration.app_label != app_name:
            return old_basedir(self)

        # Ensure
        migrations_dir = settings.BASE_DIR / settings.MIGRATION_MODULES[app_name]
        migrations_dir.mkdir(parents=True, exist_ok=True)
        return str(migrations_dir)

    def new_load_disk(self):
        old_load_disk(self)

    MigrationWriter.basedir = property(new_basedir)  # type: ignore
    MigrationLoader.load_disk = new_load_disk


def patch_db(app_name):
    patch_modelbase(app_name)
    patch_migrations(app_name)
