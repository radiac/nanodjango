from __future__ import annotations

import ast
import inspect
from typing import TYPE_CHECKING, Any, Callable, cast

from django.http import HttpResponse

from .utils import (
    applied_ensure_http_response,
    collect_references,
    filter_decorators,
    is_admin_decorator,
    is_api_decorator,
    is_view_decorator,
    make_url,
    obj_to_ast,
    parse_admin_decorator,
)


if TYPE_CHECKING:
    from .converter import Converter


class ConverterObject:
    def __init__(self, converter: Converter, name: str, obj):
        self.converter = converter
        self.name = name
        self.obj = obj
        self.src = self.src_orig = inspect.getsource(obj)
        self.ast: ast.AST = obj_to_ast(self.src)
        self.references: set[str] = set()

    def remove_decorators(self, filter_fn: Callable) -> list[ast.AST]:
        """
        Remove certain decorators from the object, update self.src and self.ast, and
        return a list of removed decorators.
        """
        self.ast = cast(ast.FunctionDef | ast.ClassDef, self.ast)
        filtered_decorators, other_decorators = filter_decorators(
            self.ast,
            filter_fn,
            app_name=self.converter.app._instance_name,
        )

        self.ast.decorator_list = other_decorators
        self.src = ast.unparse(self.ast)

        return filtered_decorators

    def collect_references(self):
        self.references = collect_references(self.ast)


class AppView(ConverterObject):
    pattern: str
    url_config: dict[str, Any]

    def __init__(
        self,
        converter: Converter,
        obj: Callable,
        pattern: str,
        url_config: dict[str, Any],
    ):
        super().__init__(converter, obj.__name__, obj)
        self.pattern = pattern
        self.url_config = url_config

        # Clear all route decorators
        self.remove_decorators(is_view_decorator)

        self.fix_return_value()
        self.collect_references()

    def fix_return_value(self):
        """
        nanodjango allows string return values; this method tries to ensure the views
        that we generate for Django return an HttpResponse
        """
        # We don't decorate CBVs
        if inspect.isclass(self.obj):
            return

        # Find annotation
        if not callable(self.obj):
            raise ValueError("Unrecognised object registered as a view route")

        annotation = inspect.signature(self.obj).return_annotation
        if issubclass(annotation, HttpResponse):
            # We're already returning an HttpResponse, no changes to make
            return

        # We could be returning a string - add the decorator
        self.ast = cast(ast.FunctionDef, self.ast)
        self.ast.decorator_list.append(applied_ensure_http_response)
        self.src = ast.unparse(self.ast)

    def make_url(self) -> str:
        view_fn = f"views.{self.name}"
        if inspect.isclass(self.obj):
            view_fn = f"{view_fn}.as_view()"

        return make_url(self.pattern, view_fn, **self.url_config)


class AppModel(ConverterObject):
    admin_decorator: ast.AST | None

    def __init__(self, converter: Converter, name, obj):
        super().__init__(converter, name, obj)

        # Find any admin decorator
        admin_decorators = self.remove_decorators(is_admin_decorator)
        if len(admin_decorators) > 1:
            raise ValueError(
                f"Found more than one admin decorator on model {self.name}"
            )
        self.admin_decorator = admin_decorators[0] if admin_decorators else None

        self.collect_references()

    def __repr__(self) -> str:
        return f"<AppModel: {self.name}>"

    def make_model_admin(self) -> str:
        if not self.admin_decorator or not (
            options := parse_admin_decorator(
                self.admin_decorator,
                app_name=self.converter.app._instance_name,
            )
        ):
            return f"admin.site.register({self.name})"

        lines = [
            f"@admin.register({self.name})",
            f"class {self.name}Admin(admin.ModelAdmin):",
        ]
        lines.extend([f"    {key} = {value}" for key, value in options.items()])

        return "\n".join(lines)


class AppApiView(ConverterObject):
    def __init__(
        self,
        converter: Converter,
        name: str,
        obj: Any,
        obj_src: str,
        obj_ast: ast.AST,
    ):
        self.converter = converter
        self.name = name
        self.obj = obj
        self.src = self.src_orig = obj_src
        self.ast: ast.AST = obj_ast
        self.references: set[str] = set()

        # Process
        self.fix_return_value()
        self.collect_references()

    def fix_return_value(self):
        """
        Rewrite @app.api.method to @api.method

        AST structure is:

            Call(
                func=Attribute(
                    value=Attribute(
                        value=Name(id='app'),
                        attr='api',
                    ),
                    attr='get',
                args=[Constant(value='/add')],
                keywords=[]
            )
        """
        for decorator in self.ast.decorator_list:
            if is_api_decorator(decorator, app_name=self.converter.app._instance_name):
                decorator.func.value = decorator.func.value.value
                decorator.func.value.id = "api"

        self.src = ast.unparse(self.ast)
