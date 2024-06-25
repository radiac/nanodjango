from __future__ import annotations

import ast
import importlib.util
import inspect
from functools import wraps
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, cast

from django.http import HttpResponse

from .reference import ReferenceVisitor


def pp_ast(obj_ast: ast.AST):
    """
    Development aid to pretty-print an AST object
    """
    print(ast.dump(obj_ast, indent=2))


def import_from_path(module_name: str, file_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if not spec or spec.loader is None:
        raise ValueError(f"spec_from_file_location failed for {file_path}")
    module = importlib.util.module_from_spec(spec)
    return module


def obj_to_ast(obj_src: str) -> ast.AST:
    """
    Convert a single object into its AST

    ast.parse returns an ast.Module with a body of 1; this confirms a single object was
    parsed, extracts and returns it
    """
    obj_ast_module = ast.parse(obj_src)
    if not isinstance(obj_ast_module, ast.Module) or len(obj_ast_module.body) != 1:
        raise ValueError(
            f"Object source does not seem to be a single object: {obj_src}"
        )
    obj_ast = obj_ast_module.body[0]
    return obj_ast


def collect_references(node: ast.AST) -> set[str]:
    visitor = ReferenceVisitor()
    visitor.visit(node)
    return visitor.globals_ref


def get_decorators(obj_ast: ast.AST) -> list[ast.AST]:
    all_decorators = getattr(obj_ast, "decorator_list", [])
    return all_decorators


def filter_decorators(
    obj_ast: ast.FunctionDef | ast.ClassDef, filter_fn: Callable, app_name: str
) -> tuple[list[ast.AST], list[ast.AST]]:
    matches = []
    others = []
    for decorator in get_decorators(obj_ast):
        if filter_fn(decorator, app_name=app_name):
            matches.append(decorator)
        else:
            others.append(decorator)
    return matches, others


def parse_admin_decorator(obj_ast: ast.AST, app_name: str) -> dict[str, Any]:
    keywords: dict[str, Any] = {}
    if isinstance(obj_ast, ast.Call):
        keywords = {}

        for keyword in obj_ast.keywords:
            if not isinstance(keyword.arg, str):
                raise ValueError(
                    f"Unrecognised @{app_name}.admin argument: {ast.unparse(keyword)}"
                )
            keywords[keyword.arg] = ast.unparse(keyword.value)
        obj_ast = obj_ast.func

    if (
        isinstance(obj_ast, ast.Attribute)
        and isinstance(obj_ast.value, ast.Name)
        and obj_ast.value.id == app_name
        and obj_ast.attr == "admin"
    ):
        return keywords

    raise ValueError(
        f"Unrecognised @{app_name}.admin definition: {ast.unparse(obj_ast)}"
    )


def mk_app_decorator_filter(attr_name: str) -> Callable:
    def filter_fn(obj_ast: ast.AST, app_name: str) -> bool:
        # Match by string - avoids having to deal with AST complexities caused by
        # * calls, eg @app.route(...)
        # * nested decorators, eg @app.api.get(...)
        src = ast.unparse(obj_ast).strip()
        seek = f"{app_name}.{attr_name}"
        if src.startswith(seek) and (len(src) == len(seek) or src[len(seek)] in ".("):
            return True
        return False

    return filter_fn


is_admin_decorator = mk_app_decorator_filter("admin")
is_view_decorator = mk_app_decorator_filter("route")
is_api_decorator = mk_app_decorator_filter("api")


def ensure_http_response(view_fn):
    """
    If a view returns a plain string value, convert it into an HttpResponse
    """

    @wraps(view_fn)
    def wrapped(*args, **kwargs):
        response = view_fn(*args, **kwargs)
        if isinstance(response, HttpResponse):
            return response
        return HttpResponse(response)

    return wrapped


# Dependencies for ReferenceVisitor to find
setattr(
    ensure_http_response,
    "_dependencies",
    {
        "wraps": "from functools import wraps",
        "HttpResponse": "from django.http import HttpResponse",
    },
)


@ensure_http_response
def decorated():
    pass


applied_ensure_http_response = cast(
    ast.FunctionDef, obj_to_ast(inspect.getsource(decorated))
).decorator_list[0]


# Generate a line for an url_patterns
def make_url(pattern, view_fn, re=False, include=None, name=None, **url_config):
    # TODO: We should probably escape self.pattern, but it's an extreme edge case
    # that doesn't seem worth the effort at the moment. Contributions welcome.
    if re:
        path_fn = "re_path"
        r = "r"
    else:
        path_fn = "path"
        r = ""

    if name is not None:
        name_arg = f', name="{name}"'
    else:
        name_arg = ""

    return f'    {path_fn}({r}"{pattern}", {view_fn}{name_arg}),'
