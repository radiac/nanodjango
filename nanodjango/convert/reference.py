from __future__ import annotations

import ast
from collections import defaultdict


class ReferenceVisitor(ast.NodeVisitor):
    """
    Visitor to traverse the AST of a class or function, looking for references to
    objects outside its scope
    """

    # This class is likely incomplete. Contributions welcome.

    #: Set of global names referenced
    globals_ref: set[str]

    #: Lookup of which nodes reference each global
    globals_lookup: dict[str, list[ast.AST]]

    def __init__(self):
        self.locals_stack = [set()]
        self.globals_ref = set()
        self.globals_lookup = defaultdict(list)

    def push_scope(self):
        self.locals_stack.append(self.current_scope.copy())

    def pop_scope(self):
        self.locals_stack.pop()

    @property
    def current_scope(self):
        return self.locals_stack[-1]

    @property
    def local_scopes(self):
        return set().union(*self.locals_stack)

    def found_reference(self, node):
        ref = node.id
        if ref in __builtins__:
            return
        if ref not in self.local_scopes:
            self.globals_ref.add(ref)
        self.globals_lookup[ref].append(node)

    def visit_FunctionDef(self, node):
        """Function definition, including top level definition if obj is a function"""
        self.current_scope.add(node.name)

        # Find all new local args in fn definition
        args = node.args.args + node.args.kwonlyargs
        if node.args.vararg:
            args.append(node.args.vararg)
        if node.args.kwarg:
            args.append(node.args.kwarg)

        self.push_scope()
        for arg in args:
            self.current_scope.add(arg.arg)

        for decorator in node.decorator_list:
            self.visit(decorator)
        self.generic_visit(node)
        self.pop_scope()

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        """Function definition, including top level definition if obj is a class"""
        self.push_scope()
        for base in node.bases:
            self.visit(base)
        for decorator in node.decorator_list:
            self.visit(decorator)
        for stmt in node.body:
            self.visit(stmt)
        self.pop_scope()

    def visit_Assign(self, node):
        """Direct variable assignments"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.current_scope.add(target.id)
            elif isinstance(target, ast.Tuple):
                # Handle tuple unpacking: foo, bar = fn()
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self.current_scope.add(elt.id)
        self.generic_visit(node)

    def visit_NamedExpr(self, node):
        """Walrus operator assignment"""
        if isinstance(node.target, ast.Name):
            self.current_scope.add(node.target.id)
        self.visit(node.value)

    def visit_Attribute(self, node):
        """Accessing an attribute of a variable"""
        if isinstance(node.value, ast.Name):
            node.value.attribute_parent = node
            self.found_reference(node.value)
        self.visit(node.value)

    def visit_Name(self, node):
        """Accessing something in scope, eg a variable"""
        if isinstance(node.ctx, ast.Load):
            self.found_reference(node)

    def visit_Global(self, node):
        """Bringing in a global reference"""
        for name in node.names:
            self.found_reference(node)

    def visit_ListComp(self, node: ast.ListComp | ast.SetComp | ast.GeneratorExp):
        """List and set comprehensions, and generator expressions"""
        self.push_scope()
        for generator in node.generators:
            self.visit(generator)
        self.visit(node.elt)
        self.pop_scope()

    visit_SetComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp

    def visit_DictComp(self, node):
        """Dictionary comprehension"""
        self.push_scope()
        for generator in node.generators:
            self.visit(generator)
        self.visit(node.key)
        self.visit(node.value)
        self.pop_scope()

    def visit_With(self, node):
        """With statement context managers"""
        # Visit the context manager expressions first
        for item in node.items:
            self.visit(item.context_expr)
            # Add the 'as' variable to local scope if it exists
            if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                self.current_scope.add(item.optional_vars.id)
        # Then visit the body
        for stmt in node.body:
            self.visit(stmt)

    def visit_ExceptHandler(self, node):
        """Exception handler with 'as' variable"""
        # Visit the exception type first
        if node.type:
            self.visit(node.type)
        # Add the 'as' variable to local scope if it exists
        if node.name:
            self.current_scope.add(node.name)
        # Then visit the body
        for stmt in node.body:
            self.visit(stmt)

    def visit_Import(self, node: ast.Import | ast.ImportFrom):
        for alias in node.names:
            if alias.asname:
                self.current_scope.add(alias.asname)
            else:
                self.current_scope.add(alias.name)

    visit_ImportFrom = visit_Import
