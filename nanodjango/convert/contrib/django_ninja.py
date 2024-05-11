from __future__ import annotations

import ast

from ..converter import Converter, Resolver
from ..plugin import ConverterPlugin
from ..utils import collect_references, get_decorators


class NinjaConverter(ConverterPlugin):
    def build_app_models_done(self, converter: Converter) -> None:
        """
        Find uses of NinjaAPI instances and move them into api.py
        """
        resolver = Resolver(converter, ".api")
        api_objs = set()
        code = []

        for obj_ast in converter.ast.body:
            is_ninja = False

            if (
                isinstance(obj_ast, ast.Assign)
                and isinstance(obj_ast.value, ast.Call)
                and isinstance(obj_ast.value.func, ast.Name)
                and obj_ast.value.func.id == "NinjaAPI"
            ):
                for target in obj_ast.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        api_objs.add(name)
                        resolver.add_object(name)

                is_ninja = True

            elif isinstance(obj_ast, ast.FunctionDef):
                decorators = get_decorators(obj_ast)
                for decorator in decorators:
                    if isinstance(decorator, ast.Call):
                        decorator = decorator.func

                    if (
                        isinstance(decorator, ast.Attribute)
                        and isinstance(decorator.value, ast.Name)
                        and decorator.value.id in api_objs
                    ):
                        resolver.add_object(obj_ast.name)
                        is_ninja = True

            if is_ninja:
                src = ast.unparse(obj_ast)
                references = collect_references(obj_ast)
                resolver.add_references(references)
                code.append(src)

        if not api_objs:
            return

        converter.write_file(
            converter.app_path / "api.py",
            resolver.gen_src(),
            "\n".join(code),
        )
