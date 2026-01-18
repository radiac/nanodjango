"""
Deferred import system for nanodjango.

This module provides the infrastructure to defer Django imports until after
Django is configured, solving the circular dependency problem in single-file
applications.
"""

from __future__ import annotations

import ast
import dis
import inspect
import traceback
from contextlib import contextmanager
from importlib.util import find_spec
from types import FrameType, ModuleType
from typing import Any, Generator


class DeferredUsageError(ImportError):
    """
    Raised when trying to use a deferred import before it's applied
    """


class DeferredImport:
    """
    Represents a deferred import statement
    """

    def __init__(
        self,
        module_name: str,
        target_globals: dict[str, Any],
        line: str = "",
        alias: str | None = None,
        from_name: str | None = None,
        from_alias: str | None = None,
        optional: bool = False,
    ):
        self.module_name = module_name
        self.target_globals = target_globals
        self.line = line
        self.alias = alias
        self.from_name = from_name
        self.from_alias = from_alias
        self.optional = optional

        # Capture the original stack trace in case we need to raise an error
        # TODO: Find a better way
        # *Stack extraction can fail in environments where modules are in zip files.
        # * This probably needs a new approach
        try:
            self.original_stack = traceback.extract_stack()[:-2]
        except Exception:
            self.original_stack = []

    @property
    def name(self):
        return self.from_alias or self.from_name or self.alias or self.module_name

    def __repr__(self):
        if self.optional:
            base = f"<[Optional] {self.name}: {self.line}>"
        else:
            base = f"<{self.name}: {self.line}>"
        return base


class DeferredImportErrorMixin(Exception):
    """
    Mixin to add deferred import location info to exceptions
    """

    def __init__(self, original_error: Exception, deferred: DeferredImport):
        # Find the frame that contains the actual import
        import_frame = None
        for frame_summary in reversed(deferred.original_stack):
            if frame_summary.line and "import " in frame_summary.line:
                import_frame = frame_summary
                break

        if not import_frame and deferred.original_stack:
            import_frame = deferred.original_stack[-1]

        # Enhance the original message with location info if available
        source = ""
        if import_frame:
            source = f'\n  File "{import_frame.filename}", line {import_frame.lineno}, in {import_frame.name}'

        enhanced_message = f"{original_error}{source}\n    {deferred.line}"

        super().__init__(enhanced_message)
        self.original_error = original_error
        self.deferred = deferred


class DeferredImportError(DeferredImportErrorMixin, ImportError):
    pass


class DeferredModuleNotFoundError(DeferredImportErrorMixin, ModuleNotFoundError):
    pass


class DeferredAttributeError(DeferredImportErrorMixin, AttributeError):
    pass


class ImportDeferrer:
    """
    Manages deferred imports by intercepting Python's import mechanism.

    This class is used as a context manager to defer imports until after Django
    is configured. Use the global ``defer`` instance rather than creating your own.

    Example::

        from nanodjango.defer import defer

        with defer:
            from django.db import models

        # Later, after Django setup
        defer.apply()
    """

    #: Whether the deferrer is currently intercepting imports
    active: bool
    #: List of deferred imports to execute later
    deferred_imports: list[DeferredImport]
    #: Reference to the original __import__ function
    original_import: Any | None
    #: Globals dict from the calling context
    caller_globals: dict[str, Any] | None
    #: Whether we're in optional import mode
    _optional_mode: bool
    #: Cache for file contents
    file_cache: dict[str, list[str]]

    def __init__(self):
        self.active = False
        self.deferred_imports = []
        self.original_import = None
        self.caller_globals = None
        self._optional_mode = False
        self.file_cache = {}

    @property
    @contextmanager
    def optional(self) -> Generator[None, None, None]:
        """
        Context manager for optional imports that won't raise errors if unavailable.

        Use this for conditional features that depend on optional packages.

        Example::

            with defer:
                with defer.optional:
                    from django_extensions.models import TimeStampedModel

            # After defer.apply(), TimeStampedModel will be None if
            # django-extensions is not installed
        """
        was_active = self.active
        if not was_active:
            self.__enter__()

        old_optional_mode = self._optional_mode
        self._optional_mode = True
        try:
            yield
        finally:
            self._optional_mode = old_optional_mode
            if not was_active and self.active:
                self.__exit__(None, None, None)

    def __enter__(self) -> ImportDeferrer:
        """
        Start deferring imports.

        Returns the deferrer instance and begins intercepting all import statements.

        Returns:
            Self
        """
        if self.active:
            return self

        self.active = True
        if self.deferred_imports is None:
            self.deferred_imports = []

        # Get the caller's frame to access their globals
        frame = inspect.currentframe()
        if frame is None:
            raise RuntimeError("Cannot access current frame")
        caller_frame = frame.f_back
        if caller_frame is None:
            raise RuntimeError("Cannot access caller frame")
        self.caller_globals = caller_frame.f_globals

        # Replace the built-in __import__ function
        self.original_import = __builtins__["__import__"]
        __builtins__["__import__"] = self._deferred_import
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """
        Stop deferring imports.

        Restores the original import function but does not execute deferred
        imports yet. Call ``apply()`` to execute them.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)

        Returns:
            False (does not suppress exceptions)
        """
        if not self.active:
            return False

        # Restore original import
        if self.original_import is None:
            raise RuntimeError("Internal error: original_import is None")
        __builtins__["__import__"] = self.original_import
        self.active = False
        return False  # Don't suppress exceptions

    def apply(self) -> None:
        """
        Execute all deferred imports.

        This must be called after exiting the context manager and after Django
        is configured. It executes all imports that were deferred and then clears
        the deferred import list.

        Raises:
            RuntimeError: If called while still deferring imports

        Example::

            with defer:
                from django.db import models

            # Django is now configured
            defer.apply()  # Imports are executed here
        """
        if self.active:
            raise RuntimeError(
                "Cannot apply imports while still deferring. Exit the context manager first."
            )

        # Execute deferred imports
        for deferred in self.deferred_imports:
            self._execute_import(deferred)

        # Clear the deferred imports after applying
        self.deferred_imports = []
        self.caller_globals = None
        self.file_cache = {}  # Clear cache when done

    def _deferred_import(
        self,
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple = (),
        level: int = 0,
    ) -> Any:
        """
        Custom import function that defers imports instead of executing them
        """
        if self.original_import is None:
            raise RuntimeError("Not in context, original_import is None")
        if self.caller_globals is None:
            raise RuntimeError("Not in context, caller_globals is None")

        if not self.active:
            return self.original_import(name, globals, locals, fromlist, level)

        target_globals = globals if globals is not None else self.caller_globals
        frame = inspect.currentframe()
        if frame is None:
            raise RuntimeError("Cannot access current frame")
        caller_frame = frame.f_back
        if caller_frame is None:
            raise RuntimeError("Cannot access caller frame")

        try:
            # Get the source line to find any aliases
            line = self._extract_import(caller_frame, name)

        except Exception as e:
            # If we can't parse the import properly, this is a serious problem
            # for aliases, so raise an error
            raise RuntimeError(f"Failed to parse import statement for '{name}'") from e

        if not line:
            raise RuntimeError(
                f"Cannot determine import statement for '{name}' - no code context available"
            )

        # Special case for Python 3.13+, which imports standard lib during our
        # resolution process. It's fine for us to skip these standard libs.
        if line in ["import os", "import sys", "import tokenize"]:
            return self.original_import(name, globals, locals, fromlist, level)

        for deferred_kwargs in self._parse_import_line(line, name):
            deferred = DeferredImport(
                target_globals=target_globals,
                line=line,
                **deferred_kwargs,
            )
            self.deferred_imports.append(deferred)

        dummy_module = DummyObject(name)
        return dummy_module

    def _extract_import(self, frame: FrameType, name: str) -> str | None:
        """
        Extract import statement from bytecode
        """
        code = frame.f_code
        lasti = frame.f_lasti

        # Get all instructions
        instructions = list(dis.get_instructions(code))

        # Find the current instruction position
        current_instruction_index = 0
        for i, instr in enumerate(instructions):
            if instr.offset <= lasti:
                current_instruction_index = i
            else:
                break

        # Look backwards and forwards from current position for import-related instructions
        import_instructions = []
        store_instructions = []

        # Search around the current instruction for IMPORT and STORE operations
        search_start = max(0, current_instruction_index - 10)
        search_end = min(len(instructions), current_instruction_index + 10)

        for i in range(search_start, search_end):
            instr = instructions[i]

            if instr.opname in ("IMPORT_NAME", "IMPORT_FROM"):
                import_instructions.append((i, instr))
            elif instr.opname in ("STORE_NAME", "STORE_GLOBAL", "STORE_FAST"):
                store_instructions.append((i, instr))

        # For "from module import item", we need to find both IMPORT_NAME and IMPORT_FROM
        # For "import module", we only need IMPORT_NAME

        # Look for IMPORT_NAME and IMPORT_FROM instruction pairs
        # We'll reconstruct all import statements and see which one makes sense
        for import_name_idx, import_name_instr in import_instructions:
            if import_name_instr.opname != "IMPORT_NAME":
                continue

            # The argval contains the full module path being imported
            module_name = import_name_instr.argval

            # Check if this module name starts with our name (for "from django.contrib.auth.models" when name="django")
            if not (module_name == name or module_name.startswith(name + ".")):
                continue

            # Find IMPORT_FROM instructions that follow this IMPORT_NAME
            # until we hit another IMPORT_NAME (which starts a new import statement)
            import_from_instrs = []
            next_import_name_idx = None

            # Find the next IMPORT_NAME instruction
            for idx, instr in import_instructions:
                if instr.opname == "IMPORT_NAME" and idx > import_name_idx:
                    next_import_name_idx = idx
                    break

            # Collect IMPORT_FROM instructions between this IMPORT_NAME and the next
            for idx, instr in import_instructions:
                if (
                    instr.opname == "IMPORT_FROM"
                    and idx > import_name_idx
                    and (next_import_name_idx is None or idx < next_import_name_idx)
                ):
                    import_from_instrs.append((idx, instr))

            if import_from_instrs:
                # This is "from module import name1, name2, ..." - collect all imported names
                imported_items = []

                # Find the corresponding STORE instructions for each IMPORT_FROM
                for from_idx, from_instr in import_from_instrs:
                    imported_name = from_instr.argval

                    # Find the STORE instruction that follows this IMPORT_FROM
                    target_store = None
                    for store_idx, store_instr in store_instructions:
                        if store_idx > from_idx:
                            target_store = store_instr
                            break

                    if target_store:
                        target_name = target_store.argval
                        if target_name == imported_name:
                            imported_items.append(imported_name)
                        else:
                            imported_items.append(f"{imported_name} as {target_name}")

                if imported_items:
                    return f"from {module_name} import {', '.join(imported_items)}"
            else:
                # This is "import module [as alias]" - find the STORE instruction
                target_store = None
                for idx, instr in store_instructions:
                    if idx > import_name_idx:
                        target_store = instr
                        break

                if target_store:
                    target_name = target_store.argval
                    if target_name == module_name:
                        return f"import {module_name}"
                    else:
                        return f"import {module_name} as {target_name}"

        # If we can't determine the exact pattern, check variable names in frame
        # to see if there's an alias being created
        frame_vars = set(frame.f_locals.keys()) | set(frame.f_globals.keys())

        # If the module name itself isn't being stored but something else is,
        # it might be an alias
        potential_aliases = [
            var for var in frame_vars if var != name and not var.startswith("_")
        ]

        if potential_aliases and len(potential_aliases) == 1:
            alias = potential_aliases[0]
            return f"import {name} as {alias}"

        # Import bytecode analysis failed
        raise RuntimeError(f"Unable to determine import statement for {name=}")

    def _parse_import_line(self, line: str, name: str):
        """
        Generator to parse the import line and return kwargs for each DeferredImport
        """
        tree = ast.parse(line)
        if tree.body and isinstance(tree.body[0], (ast.Import, ast.ImportFrom)):
            stmt = tree.body[0]

            if isinstance(stmt, ast.Import):
                # Handle "import module" or "import module as alias"
                for alias in stmt.names:
                    yield {
                        "module_name": alias.name,
                        "alias": alias.asname,
                        "optional": self._optional_mode,
                    }

            elif isinstance(stmt, ast.ImportFrom):
                # Handle "from module import name" or "from module import name as alias"
                for alias in stmt.names:
                    yield {
                        "module_name": stmt.module,
                        "from_name": alias.name,
                        "from_alias": alias.asname,
                        "optional": self._optional_mode,
                    }

    def _execute_import(self, deferred: DeferredImport):
        """
        Execute a single deferred import
        """
        target_globals = deferred.target_globals

        # Calculate target name once
        if deferred.from_name:
            target_name = (
                deferred.from_alias if deferred.from_alias else deferred.from_name
            )
        else:
            target_name = deferred.alias if deferred.alias else deferred.module_name

        try:
            if deferred.from_name:
                # Handle "from module import name [as alias]"
                # For "from module import name", we need to pass fromlist to get the leaf module
                module = self.original_import(
                    deferred.module_name, target_globals, {}, [deferred.from_name], 0
                )
                target_obj = getattr(module, deferred.from_name)
            else:
                # Handle "import module [as alias]"
                target_obj = self.original_import(deferred.module_name, target_globals)

        except (ImportError, ModuleNotFoundError, AttributeError) as e:
            if deferred.optional:
                target_obj = None
            else:
                if isinstance(e, ModuleNotFoundError):
                    raise DeferredModuleNotFoundError(e, deferred)
                elif isinstance(e, AttributeError):
                    raise DeferredAttributeError(e, deferred)
                else:
                    raise DeferredImportError(e, deferred)

        # Set the final value once
        target_globals[target_name] = target_obj

    @classmethod
    def is_installed(cls, package_name: str) -> bool:
        """
        Check if a package is available for import.

        Args:
            package_name: The name of the package as installed (e.g. 'requests',
                         'django'). Same name used with 'pip install package_name'

        Returns:
            True if the package is installed and can be imported, False otherwise

        Example::

            if defer.is_installed("requests"):
                # Use requests features
                pass

            if defer.is_installed("django-ninja"):
                # Use django-ninja features
                pass
        """
        spec = find_spec(package_name)
        return spec is not None


class DummyObject:
    """
    A dummy object that raises an error when called or used
    """

    def __init__(self, name):
        self.name = name

    def __getattr__(self, attr_name):
        return type(self)(f"{self.name}.{attr_name}")

    def _raise_error(self):
        raise DeferredUsageError(
            f"Cannot use deferred import '{self.name}' until defer.apply() is called"
        )

    def __call__(self, *args, **kwargs):
        self._raise_error()

    def __str__(self):
        self._raise_error()

    def __repr__(self):
        self._raise_error()

    def __bool__(self):
        self._raise_error()


# Global instance - use as context manager: with defer: ...
defer = ImportDeferrer()
