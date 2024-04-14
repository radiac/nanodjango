from __future__ import annotations

import ast
import inspect
from typing import Callable, cast

from django.http import HttpResponse

from .utils import (
    applied_ensure_http_response,
    collect_references,
    is_admin_decorator,
    is_view_decorator,
    obj_to_ast,
    parse_admin_decorator,
)


class ConverterObject:
    def __init__(self, name: str, obj):
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
        all_decorators = getattr(self.ast, "decorator_list", [])
        filtered_decorators = []
        if not all_decorators:
            return []

        self.ast = cast(ast.FunctionDef | ast.ClassDef, self.ast)
        self.ast.decorator_list = []
        for decorator in all_decorators:
            if filter_fn(decorator):
                filtered_decorators.append(decorator)
            else:
                self.ast.decorator_list.append(decorator)
        self.src = ast.unparse(self.ast)

        return filtered_decorators

    def collect_references(self):
        self.references = collect_references(self.ast)


class AppView(ConverterObject):
    pattern: str

    def __init__(self, pattern, obj):
        super().__init__(obj.__name__, obj)
        self.pattern = pattern

        # Clear all route decorators
        self.remove_decorators(is_view_decorator)

        self.fix_return_value()
        self.collect_references()

    def fix_return_value(self):
        """
        nanodjango allows string return values; this method tries to ensure the views
        that we generate for Django return an HttpResponse
        """
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
        # TODO: We should probably escape self.pattern, but it's an extreme edge case
        # that doesn't seem worth the effort at the moment. Contributions welcome.
        return f'    path("{self.pattern}", views.{self.name}),'


class AppModel(ConverterObject):
    admin_decorator: ast.AST | None

    def __init__(self, name, obj):
        super().__init__(name, obj)

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
            options := parse_admin_decorator(self.admin_decorator)
        ):
            return f"admin.site.register({self.name})"

        lines = [
            f"@admin.register({self.name})",
            f"class {self.name}Admin(admin.ModelAdmin):",
        ]
        lines.extend([f"    {key} = {value}" for key, value in options.items()])

        return "\n".join(lines)
