from __future__ import annotations

import ast
import inspect
import os
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, cast

import isort
from black import FileMode, format_str
from django.db.models import Model

from ..exceptions import ConversionError
from .objects import AppModel, AppView
from .utils import collect_references, ensure_http_response, import_from_path

if TYPE_CHECKING:
    from pathlib import Path

    from ..app import Django


class Resolver:
    imports: set[str]
    local_refs: set[str]
    global_refs: set[str]

    def __init__(self, converter: Converter, module_name: str):
        self.converter = converter
        self.module_name = module_name

        self.imports = set()
        self.local_refs = set()
        self.global_refs = set()

    def add(self, name: str, references: set[str]):
        # Log this object definition
        self.converter.imports[name] = f"from {self.module_name} import {name}"
        self.local_refs.add(name)

        self.add_references(references)

    def add_references(self, references: set[str]):
        # Collect import and global references
        for ref in references:
            if ref in self.local_refs:
                pass
            elif ref in self.converter.imports:
                self.imports.add(self.converter.imports[ref])
            else:
                self.global_refs.add(ref)

    def gen_src(self):
        all_src = []
        global_refs = self.global_refs.copy()
        while self.global_refs:
            # Collect the source for the reference, and grab any references it may have
            global_ref = self.global_refs.pop()
            src, references = self.converter.collect_definition(global_ref)
            all_src.append(src)

            # Record references from this
            self.add_references(references)

            # We may have added references to locals we have seen before - remove them
            self.global_refs = self.global_refs - self.local_refs

            # The global reference is now local
            self.local_refs.add(global_ref)

            # Tell other modules where to find it
            self.converter.imports[
                global_ref
            ] = f"from {self.module_name} import {global_ref}"

        # Restore global refs
        self.global_refs = global_refs
        return "\n".join(list(self.imports) + all_src)


class Converter:
    #: AppModel instances for models that are being moved to models.py
    models: list[AppModel]

    #: AppView instances for views that are being moved to views.py
    views: list[AppView]

    #: Import paths - existing imports in the app, plus converted models and views
    imports: dict[str, str]

    #: Definitions in the module's top level scope which have been converted
    used: set[str]

    def __init__(self, app: Django, path: Path, name: str):
        self.app = app
        self.root_path = path
        self.project_name = name
        self.module = app.app_module
        self.src = inspect.getsource(app.app_module)
        self.ast = ast.parse(self.src)
        self.used = set()

        self.collect_imports()

    def write_file(self, filename: str | Path, *content):
        path = Path(filename)
        formatted = isort.code(format_str("\n".join(content), mode=FileMode()))
        path.write_text(formatted)

    def write(self) -> None:
        self.build_project()
        self.build_app_models()
        self.build_app_views()
        self.build_app_urls()
        self.build_app_admin()
        self.build_app_unused()

    def build_project(self) -> None:
        # Copy the env, so we're still working within any venv
        env = os.environ.copy()
        env.pop("DJANGO_SETTINGS_MODULE", None)
        try:
            result = subprocess.run(
                ["django-admin", "startproject", self.project_name, self.root_path],
                env=env,
                capture_output=True,
                text=True,
            )
        except Exception as e:
            raise ConversionError(f"Could not run django-admin: {e}")

        if result.returncode != 0:
            raise ConversionError(f"django-admin startproject failed: {result.stderr}")

        # Create app dir
        app_dir = self.root_path / self.project_name / self.app.app_name
        app_dir.mkdir()
        (app_dir / "__init__.py").touch()

        self.build_settings()
        self.build_urls()
        self.copy_assets()

    def build_settings(self) -> None:
        """
        Collect settings from the app definition and update the project settings
        """
        resolver = Resolver(self, f"{self.project_name}.settings")

        # Collect from app definition and remove nanodjango-specific settings
        app_settings = {}
        for node in self.ast.body:
            # Look for app = Django(..)
            if (
                isinstance(node, ast.Assign)
                and any(
                    [
                        target.id == "app"
                        for target in node.targets
                        if isinstance(target, ast.Name)
                    ]
                )
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "Django"
            ):
                for keyword in node.value.keywords:
                    name: str = cast(str, keyword.arg)
                    if name.isupper():
                        # Exclude nanodjango-specific settings
                        if name in [
                            "ADMIN_URL",
                            "EXTRA_APPS",
                            "SQLITE_DATABASE",
                            "MIGRATIONS_DIR",
                        ]:
                            continue
                        else:
                            app_settings[name] = keyword.value
                            resolver.add_references(collect_references(keyword.value))

        # Load settings file
        filename = self.root_path / self.project_name / "settings.py"
        settings = import_from_path("nanodjango.convert.tmp_settings", filename)
        settings_src = inspect.getsource(settings)
        settings_ast = ast.parse(settings_src)

        # Replace settings
        for node in settings_ast.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if not isinstance(target, ast.Name):
                        continue
                    if target.id in app_settings:
                        node.value = app_settings.pop(target.id)

                    # Special case for INSTALLED_APPS
                    if target.id == "INSTALLED_APPS" and isinstance(
                        node.value, ast.List
                    ):
                        # Inject our converted app
                        node.value.elts.append(
                            ast.Constant(
                                value=f"{self.project_name}.{self.app.app_name}"
                            )
                        )

                        # Append any EXTRA_APPS
                        if "EXTRA_APPS" in self.app._settings:
                            for extra_app in self.app._settings["EXTRA_APPS"]:
                                node.value.elts.append(ast.Constant(value=extra_app))

        # Add any extra vars
        for name, value in app_settings.items():
            node = ast.Assign(targets=[ast.Name(id=name, ctx=ast.Store())], value=value)
            settings_ast.body.append(node)

        # Insert any references - usually imports
        ref_src = resolver.gen_src()
        if ref_src:
            imports = set()
            others = set()

            for node in ast.parse(ref_src).body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.add(node)
                else:
                    others.add(node)

            # We're expecting a comment at the top - insert imports just after that
            if (
                len(settings_ast.body) == 0
                or not isinstance(settings_ast.body[0], ast.Expr)
                or not isinstance(settings_ast.body[0].value, ast.Constant)
            ):
                raise ConversionError("Unexpected start to settings.py")
            settings_ast.body[1:1] = imports

            # Insert other definitions after the last import
            index = 0
            for node in settings_ast.body:
                if isinstance(node, (ast.Expr, ast.Import, ast.ImportFrom)):
                    index += 1
                    continue
                break
            settings_ast.body[index:index] = others

        # Save settings
        self.write_file(filename, ast.unparse(settings_ast))

    def build_urls(self) -> None:
        filename = self.root_path / self.project_name / "urls.py"
        src = filename.read_text()

        # Add path to app
        pattern = "urlpatterns = ["
        if pattern not in src:
            raise ConversionError("Expected to find urlpatterns in urls.py")
        src = src.replace(
            "from django.urls import path",
            "from django.urls import include, path",
        ).replace(
            pattern,
            f'{pattern}\n    path("", include("{self.project_name}.{self.app.app_name}.urls")),',
        )

        if "ADMIN_URL" in self.app._settings:
            pattern = '"admin/"'
            if pattern not in src:
                raise ConversionError("Expected to find admin path in urls.py")
            src = src.replace(pattern, f'"{self.app._settings["ADMIN_URL"]}"')

        self.write_file(filename, src)

    def copy_assets(self) -> None:
        """
        Copy static, templates, and migrations into app, and db.sqlite3 if it exists
        """
        script_dir = self.app.app_path.parent

        db_file = script_dir / self.app._settings.get("SQLITE_DATABASE", "db.sqlite3")
        if db_file.exists():
            shutil.copy(db_file, self.root_path / "db.sqlite3")

        dir_names = [
            "static",
            "templates",
            self.app._settings.get("MIGRATIONS_DIR", "migrations"),
        ]
        for dir_name in dir_names:
            src_dir = script_dir / dir_name
            if src_dir.exists() and src_dir.is_dir():
                shutil.copytree(
                    src_dir,
                    self.root_path / self.project_name / self.app.app_name / dir_name,
                )

    def collect_imports(self) -> dict[str, str]:
        """
        Collect a lookup for imported names

        Values are the import strings - we'll use isort to merge modules later
        """
        self.imports = {}
        for node in self.ast.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports[alias.name] = f"import {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    self.imports[alias.name] = f"from {node.module} import {alias.name}"

        return self.imports

    def collect_definition(self, obj_name) -> tuple[str, set[str]]:
        """
        Collect a definition of a module top-level scope object
        """
        if obj_name == "ensure_http_response":
            # Inject its dependencies
            self.imports.update(getattr(ensure_http_response, "_dependencies", {}))
            obj_src = inspect.getsource(ensure_http_response)
            obj_ast = ast.parse(obj_src)
            references = collect_references(obj_ast.body[0])
            return obj_src, references

        if obj_name not in self.module.__dict__:
            raise ConversionError(f"Reference to unknown symbol {obj_name}")
        obj = self.module.__dict__[obj_name]

        # Try to build src from the object
        try:
            obj_src = inspect.getsource(obj)
        except TypeError:
            # Not a class, method, function, or code object
            pass
        else:
            self.used.add(obj_name)
            obj_ast = ast.parse(obj_src)
            references = collect_references(obj_ast.body[0])
            return obj_src, references

        # Look for an assignment
        for node in self.ast.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == obj_name:
                        obj_src = ast.unparse(node).strip()
                        self.used.add(obj_name)
                        obj_ast = ast.parse(obj_src)
                        references = collect_references(obj_ast.body[0])
                        return obj_src, references

        # TODO: We could have more exhaustive definition collection
        raise ConversionError(f"Reference to undetermined symbol {obj_name}")

    def build_app_models(self) -> None:
        self.models = []
        resolver = Resolver(self, ".models")

        for name, obj in self.module.__dict__.items():
            if inspect.isclass(obj) and issubclass(obj, Model):
                app_model = AppModel(name, obj)
                self.models.append(app_model)
                resolver.add(name, app_model.references)

        if not self.models:
            return

        self.write_file(
            self.root_path / self.project_name / self.app.app_name / "models.py",
            resolver.gen_src(),
            "\n".join([app_model.src for app_model in self.models]),
        )

    def build_app_views(self) -> None:
        self.views = []
        resolver = Resolver(self, ".views")

        for pattern, view in self.app._routes.items():
            app_view = AppView(pattern, view)
            self.views.append(app_view)
            resolver.add(view.__name__, app_view.references)

        if not self.views:
            return

        self.write_file(
            self.root_path / self.project_name / self.app.app_name / "views.py",
            resolver.gen_src(),
            "\n".join([app_view.src for app_view in self.views]),
        )

    def build_app_urls(self) -> None:
        urls = []
        for app_view in self.views:
            urls.append(app_view.make_url())

        if not urls:
            return

        self.write_file(
            self.root_path / self.project_name / self.app.app_name / "urls.py",
            "from django.urls import path",
            "from . import views",
            "urlpatterns = [",
            "\n".join([src for src in urls]),
            "]",
        )

    def build_app_admin(self) -> None:
        model_names: list[str] = []
        admin_srcs: list[str] = []
        resolver = Resolver(self, ".admin")

        # Collect @app.admin decorated models
        for app_model in self.models:
            if not app_model.admin_decorator:
                continue
            model_names.append(app_model.name)
            admin_srcs.append(app_model.make_model_admin())
            resolver.add_references(set([app_model.name]))

        # TODO: We could collect ModelAdmin. For now lets let it fall into unused

        if not model_names:
            return

        self.write_file(
            self.root_path / self.project_name / self.app.app_name / "admin.py",
            "from django.contrib import admin",
            resolver.gen_src(),
            "\n".join([src for src in admin_srcs]),
        )

    def build_app_unused(self) -> None:
        resolver = Resolver(self, ".unused")

        # We're not going to worry about unused imports
        self.used.update(self.imports.keys())

        # Also going to ignore the app
        self.used.add("app")

        unused = set(self.module.__dict__.keys()) - self.used
        all_src = []
        for obj_name in unused:
            if obj_name.startswith("_"):
                continue

            # Collect the source and objects it references
            obj_src, references = self.collect_definition(obj_name)
            all_src.append(obj_src)
            resolver.add(obj_name, references)

        if not all_src:
            return

        self.write_file(
            self.root_path / self.project_name / self.app.app_name / "unused.py",
            "# Definitions that were not used by the nanodjango converter",
            "# These will need to be merged into the rest of the app manually",
            resolver.gen_src(),
            "\n".join([src for src in all_src]),
        )

        print(f"Unused code detected, see {self.app.app_name}/unused.py")
