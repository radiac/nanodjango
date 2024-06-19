from __future__ import annotations

import ast
import inspect
import os
import shutil
import subprocess
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, cast

from django.db.models import Model

import isort
from black import FileMode, format_str

from ..exceptions import ConversionError
from .objects import AppApiView, AppModel, AppView
from .plugin import plugins
from .utils import (
    collect_references,
    ensure_http_response,
    filter_decorators,
    import_from_path,
    is_api_decorator,
    make_url,
    obj_to_ast,
)


if TYPE_CHECKING:
    from pathlib import Path

    from ..app import Django


class Resolver:
    """
    Resolve names and references within the scope of the Python module we are generating
    """

    imports: set[str]
    local_refs: set[str]
    global_refs: set[str]

    def __init__(self, converter: Converter, module_name: str):
        """
        Args:
            converter (Converter): The current converter instance
            module_name (str): The name of the module we're currently building
        """
        self.converter = converter
        self.module_name = module_name

        self.imports = set()
        self.local_refs = set()
        self.global_refs = set()

    def add(self, name: str, references: set[str]):
        """
        Register an object definition, and the objects it references
        """
        self.add_object(name)
        self.add_references(references)

    def add_object(self, name: str):
        """
        Register an object that is defined in the current module we're building
        """
        self.converter.imports[name] = f"from {self.module_name} import {name}"
        self.local_refs.add(name)

    def add_references(self, references: set[str]):
        """
        Register references to symbols needed in this module - objects which will either
        need to be imported from other modules, or their source added to this module
        """
        for ref in references:
            # Most of the time this will be either an object or an imported symbol,
            # but it could be an object.child, eg admin.site.urls
            ref_base = ref.split(".", 1)[0]
            if ref_base in self.local_refs:
                pass
            elif ref_base in self.converter.imports:
                self.imports.add(self.converter.imports[ref_base])
            else:
                self.global_refs.add(ref_base)

    def gen_src(self):
        """
        Generate the source code required to resolve discovered references, either by
        copying in referenced code, or importing them from another file.
        """
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
            self.converter.imports[global_ref] = (
                f"from {self.module_name} import {global_ref}"
            )

        # Restore global refs
        self.global_refs = global_refs
        return "\n".join(list(self.imports) + all_src)


class Converter:
    #: Reference to the ``Django`` app instance
    app: Django

    #: Root path to build the project (``django-admin startproject ... {root_path}``)
    root_path: Path

    #: Name of the Django project (``django-admin startproject {project_name} ...``)
    project_name: str

    #: The module to convert
    module: ModuleType

    #: The source for the module to convert
    src: str

    #: The abstract syntax tree of the module to convert
    ast: ast.Module

    #: AppModel instances for models that are being moved to models.py
    models: list[AppModel]

    #: AppView instances for views that are being moved to views.py
    views: list[AppView]

    #: Import paths - existing imports in the app, plus converted models and views
    imports: dict[str, str]

    #: Definitions in the module's top level scope which have been converted
    used: set[str]

    def __init__(self, app: Django, path: Path, name: str):
        """
        Prepare state and load plugins
        """
        self.app = app
        self.root_path = path
        self.project_name = name
        self.module = app.app_module
        self.src = inspect.getsource(app.app_module)
        self.ast = ast.parse(self.src)

        self.models = []
        self.views = []
        self.api_views = []
        self.extra_urls = []
        self.imports = {}
        self.used = set()

        plugins.load()
        plugins.init(self)

    @property
    def project_path(self):
        return self.root_path / self.project_name

    @property
    def app_path(self):
        return self.project_path / self.app.app_name

    def write_file(self, filename: str | Path, *content):
        path = Path(filename)
        formatted = isort.code(format_str("\n".join(content), mode=FileMode()))
        path.write_text(formatted)

    def collect_definition(self, obj_name) -> tuple[str, set[str]]:
        """
        Collect a definition of a module top-level scope object

        Args:
            obj_name (str): Name of object to collect

        Returns:
            obj_src (str): Source for object
            references (set[str]): Set of referenced object names
        """
        if obj_name == "ensure_http_response":
            # Inject its dependencies
            self.imports.update(getattr(ensure_http_response, "_dependencies", {}))
            obj_src = inspect.getsource(ensure_http_response)
            obj_ast = ast.parse(obj_src)
            references = collect_references(obj_ast.body[0])
            return obj_src, references

        if obj_name not in self.module.__dict__:
            raise ValueError(f"Reference to unknown symbol {obj_name}")
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
        raise ValueError(f"Reference to undetermined symbol {obj_name}")

    def build(self) -> None:
        """
        Create the project and build the files for the project and app

        Hooks:
            build_start: Called at the start
            build_end: Called at the end
        """
        plugins.build_start(self)

        self.collect_imports()

        self.build_project()
        plugins.build_project_done(self)

        self.build_settings()
        plugins.build_settings_done(self)

        self.copy_assets()

        self.build_app_models()
        plugins.build_app_models_done(self)

        self.build_app_views()
        plugins.build_app_views_done(self)

        self.build_app_api()
        plugins.build_app_api_done(self)

        self.app_has_urls = False
        self.build_app_urls()
        plugins.build_app_urls_done(self)
        self.build_urls()
        plugins.build_urls_done(self)

        self.build_app_admin()
        plugins.build_app_admin_done(self)

        self.build_app_unused()

        plugins.build_end(self)

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

        plugins.collect_imports(self)
        return self.imports

    def build_project(self) -> None:
        """
        Run ``django-admin startproject`` and create the app dir
        """
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
        app_dir = self.app_path
        app_dir.mkdir()
        (app_dir / "__init__.py").touch()

    def build_settings(self) -> None:
        """
        Collect settings from the app definition and update the project settings

        Hooks:
            build_settings: Customise ``project/settings.py`` AST
            build_settings_done: After ``project/settings.py`` has been written
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
                        target.id == self.app._instance_name
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
        filename = self.project_path / "settings.py"
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

        # Plugin hook
        resolver, settings_ast = plugins.build_settings(self, resolver, settings_ast)

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

    def copy_assets(self) -> None:
        """
        Copy static, templates, and migrations into app, and db.sqlite3 if it exists

        Hooks:
            copy_assets: After the primary assets have been copied
        """
        script_dir = self.app.app_path.parent

        db_file = script_dir / self.app._settings.get("SQLITE_DATABASE", "db.sqlite3")
        if db_file.exists():
            shutil.copy(db_file, self.root_path / "db.sqlite3")

        # List of (source, dest)
        dir_names = [
            ("static", "static"),
            ("templates", "templates"),
            (self.app._settings.get("MIGRATIONS_DIR", "migrations"), "migrations"),
        ]
        for source_name, dest_name in dir_names:
            src_dir = script_dir / source_name
            if src_dir.exists() and src_dir.is_dir():
                shutil.copytree(
                    src_dir,
                    self.app_path / dest_name,
                )

        plugins.copy_assets(self)

    def build_app_models(self) -> None:
        """
        Build ``app/models.py`` and collect models in ``self.models`` (a list of
        ``AppModel instances).

        Hooks:
            build_app_models: Modify ``self.models`` or add content to ``app/models.py``
            build_app_models_done: After ``app/models.py`` has been written
        """
        self.models = []
        resolver = Resolver(self, ".models")

        for name, obj in self.module.__dict__.items():
            if inspect.isclass(obj) and issubclass(obj, Model):
                app_model = AppModel(self, name, obj)
                self.models.append(app_model)
                resolver.add(name, app_model.references)

        resolver, extra_src = plugins.build_app_models(self, resolver, [])

        if not self.models and not extra_src:
            return

        self.write_file(
            self.app_path / "models.py",
            resolver.gen_src(),
            "\n".join([app_model.src for app_model in self.models]),
            "\n".join(extra_src),
        )

    def build_app_views(self) -> None:
        """
        Build ``app/views.py`` and collect views in ``self.views`` (a list of
        ``AppView`` instances).

        Hooks:
            build_app_views: Modify ``self.views`` or add content to ``app/views.py``
            build_app_views_done: After ``app/views.py`` has been written.
        """
        self.views = []
        resolver = Resolver(self, ".views")

        for pattern, (view, url_config) in self.app._routes.items():
            if view is None:
                # An include
                continue
            app_view = AppView(self, view, pattern, url_config)
            self.views.append(app_view)
            resolver.add(view.__name__, app_view.references)

        resolver, extra_src = plugins.build_app_views(self, resolver, [])

        if not self.views and not extra_src:
            return

        self.write_file(
            self.app_path / "views.py",
            resolver.gen_src(),
            "\n".join([app_view.src for app_view in self.views]),
            "\n".join(extra_src),
        )

    def build_app_api(self) -> None:
        # TODO #7
        self.api_views = []
        resolver = Resolver(self, ".api")

        # API definitions will be rewritten from @app.api to @api, and we'll hard-code
        # the ``api`` definition when writing this module at the end of this method,
        # so tell the resolver we already know about ``api``
        resolver.add_object("api")

        for name, obj in self.module.__dict__.items():
            # Look at locally-defined functions
            if (
                inspect.isfunction(obj)
                and inspect.getsourcefile(obj) == self.module.__file__
            ):
                obj_src = inspect.getsource(obj)
                obj_ast = cast(ast.FunctionDef, obj_to_ast(obj_src))
                api_decorators, _ = filter_decorators(
                    obj_ast,
                    is_api_decorator,
                    self.app._instance_name,
                )
                if not api_decorators:
                    continue

                api_view = AppApiView(
                    self,
                    name=name,
                    obj=obj,
                    obj_src=obj_src,
                    obj_ast=obj_ast,
                )
                self.api_views.append(api_view)
                resolver.add(name, api_view.references)

        resolver, extra_src = plugins.build_app_api(self, resolver, [])
        if not self.api_views and not extra_src:
            return

        self.app_has_urls = True
        self.write_file(
            self.app_path / "api.py",
            "from ninja import NinjaAPI",
            resolver.gen_src(),
            "api = NinjaAPI()",
            "\n".join([api_view.src for api_view in self.api_views]),
            "\n".join(extra_src),
        )

    def build_app_urls(self) -> None:
        """
        Build ``app/urls.py``

        Hooks:
            build_app_views: Modify ``self.views`` or add content to ``app/views.py``
            build_app_views_done: After ``app/views.py`` has been written.
        """
        imports = set()
        urls = []
        resolver = Resolver(self, ".urls")

        # Add API url - this is a special case which never makes it into app._routes
        if self.api_views:
            urls.append(make_url(self.app.settings.API_URL, "api.urls"))
            resolver.add_references(["api"])

        # Add view urls
        app_views = self.views.copy()
        for pattern, (view, url_config) in self.app._routes.items():
            if app_views and app_views[0].pattern == pattern:
                # path(pattern, view)
                app_view = app_views.pop(0)
                urls.append(app_view.make_url())
            else:
                # path(pattern, include)
                # Extract the ``include`` reference
                route_ast = url_config["source"]
                if (
                    isinstance(route_ast, ast.Expr)
                    and (call := getattr(route_ast, "value"))
                    and isinstance(call, ast.Call)
                    and call.keywords
                    and (
                        include_ast := cast(
                            ast.Attribute,
                            next(kw for kw in call.keywords if kw.arg == "include"),
                        )
                    )
                ):
                    # Collect references, in case this is an include(..) call etc.
                    include_src = ast.unparse(include_ast.value)
                    references = collect_references(include_ast.value)
                    urls.append(make_url(pattern, include_src, **url_config))
                    resolver.add_references(references)
                else:
                    raise ConversionError(
                        f"Could not understand route {url_config['source']}"
                    )
            if url_config["re"]:
                imports.add("re_path")
            else:
                imports.add("path")

        resolver, urls, extra_src = plugins.build_app_urls(self, resolver, urls, [])

        if not urls and not extra_src:
            return

        # Register that we found URLs so build_urls() will link to app.urls.urlpatterns
        self.app_has_urls = True

        views_import = "from . import views"
        if not self.views:
            # We've got a urls.py which doesn't have any views - eg a plugin has added
            # extra_views or given us extra URLs
            views_import = ""

        self.write_file(
            self.app_path / "urls.py",
            f"from django.urls import {', '.join(imports)}",
            views_import,
            resolver.gen_src(),
            "urlpatterns = [",
            "\n".join(self.extra_urls),
            "\n".join(urls),
            "]",
            "\n".join(extra_src),
        )

    def build_urls(self) -> None:
        """
        Update ``project/urls.py``

        Hooks:
            build_urls: Modify source for ``project/urls.py``
            build_urls_done: After ``project/urls.py`` has been written.
        """
        filename = self.project_path / "urls.py"
        src = filename.read_text()

        # Add path to app
        pattern = "urlpatterns = ["
        if pattern not in src:
            raise ConversionError("Expected to find urlpatterns in urls.py")

        if self.app_has_urls:
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

        src = plugins.build_urls(self, src)
        self.write_file(filename, src)

    def build_app_admin(self) -> None:
        """
        Write discovered model admin registrations in ``app/admin.py``

        Hooks:
            build_app_admin: Modify or add content to ``app/admin.py``
            build_app_admin_done: After ``app/admin.py`` has been written.
        """
        model_names: list[str] = []
        admins: list[str] = []
        resolver = Resolver(self, ".admin")

        # Collect @app.admin decorated models
        for app_model in self.models:
            if not app_model.admin_decorator:
                continue
            model_names.append(app_model.name)
            admins.append(app_model.make_model_admin())
            resolver.add_references(set([app_model.name]))

        # TODO: We could collect ModelAdmin. For now lets let it fall into unused

        resolver, admins, extra_src = plugins.build_app_admin(
            self, resolver, admins, []
        )

        if not model_names:
            return

        self.write_file(
            self.app_path / "admin.py",
            "from django.contrib import admin",
            resolver.gen_src(),
            "\n".join(admins),
            "\n".join(extra_src),
        )

    def build_app_unused(self) -> None:
        """
        Write unused code into``app/unused.py``

        Hooks:
            build_app_unused: Modify or add content to ``app/unused.py``
        """
        resolver = Resolver(self, ".unused")

        # We're not going to worry about unused imports
        self.used.update(self.imports.keys())

        # Also going to ignore the app
        self.used.add(self.app._instance_name)

        unused = set(self.module.__dict__.keys()) - self.used
        all_src = []
        for obj_name in unused:
            if obj_name.startswith("_"):
                continue

            # Collect the source and objects it references
            obj_src, references = self.collect_definition(obj_name)
            all_src.append(obj_src)
            resolver.add(obj_name, references)

        resolver, extra_src = plugins.build_app_unused(self, resolver, [])

        if not all_src or extra_src:
            return

        self.write_file(
            self.app_path / "unused.py",
            "# Definitions that were not used by the nanodjango converter",
            "# These will need to be merged into the rest of the app manually",
            resolver.gen_src(),
            "\n".join(all_src),
            "\n".join(extra_src),
        )

        print(f"Unused code detected, see {self.app.app_name}/unused.py")
