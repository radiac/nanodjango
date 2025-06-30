from __future__ import annotations

import ast
import inspect
import traceback
from contextlib import contextmanager
from importlib.util import find_spec
from types import FrameType, ModuleType
from typing import Any, Dict, Generator, List, Optional, Union


class DeferredUsageError(ImportError):
    """Raised when trying to use a deferred import before it's applied"""


class DeferredImport:
    """Represents a deferred import statement"""

    def __init__(
        self,
        module_name: str,
        target_globals: Dict,
        alias: Optional[str] = None,
        from_name: Optional[str] = None,
        from_alias: Optional[str] = None,
        optional: bool = False,
    ):
        self.module_name = module_name
        self.target_globals = target_globals
        self.alias = alias
        self.from_name = from_name
        self.from_alias = from_alias
        self.optional = optional

        # Capture the original stack trace in case we need to raise an error
        self.original_stack = traceback.extract_stack()[:-2]

    def __repr__(self):
        if self.from_name:
            base = f"from {self.module_name} import {self.from_name}"
            if self.from_alias:
                base += f" as {self.from_alias}"
        else:
            base = f"import {self.module_name}"
            if self.alias:
                base += f" as {self.alias}"

        if self.optional:
            base += " (optional)"
        return base


class DeferredImportErrorMixin:
    """Mixin to add deferred import location info to exceptions"""

    def __init__(self, original_error: Exception, deferred: DeferredImport):
        # Find the frame that contains the actual import
        import_frame = None
        for frame_summary in reversed(deferred.original_stack):
            if frame_summary.line and "import " in frame_summary.line:
                import_frame = frame_summary
                break

        if not import_frame:
            import_frame = deferred.original_stack[-1]

        # Enhance the original message with location info
        original_line = (
            import_frame.line.strip()
            if import_frame.line
            else f"import {deferred.module_name}"
        )
        enhanced_message = f'{original_error}\n  File "{import_frame.filename}", line {import_frame.lineno}, in {import_frame.name}\n    {original_line}'

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
    """Manages deferred imports by intercepting the import machinery"""

    #: Whether the deferrer is currently intercepting imports
    active: bool
    #: List of deferred imports to execute later
    deferred_imports: List[DeferredImport]
    #: Reference to the original __import__ function
    original_import: Optional[Any]
    #: Globals dict from the calling context
    caller_globals: Optional[Dict[str, Any]]
    #: Whether we're in optional import mode
    _optional_mode: bool
    #: Cache for file contents
    file_cache: Dict[str, List[str]]

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
        """Context manager for optional imports"""
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
        """Start deferring imports"""
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
        """Stop deferring imports but don't execute them"""
        if not self.active:
            return False

        # Restore original import
        if self.original_import is None:
            raise RuntimeError("Internal error: original_import is None")
        __builtins__["__import__"] = self.original_import
        self.active = False
        return False  # Don't suppress exceptions

    def apply(self) -> None:
        """Execute all deferred imports"""
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
        globals: Optional[Dict[str, Any]] = None,
        locals: Optional[Dict[str, Any]] = None,
        fromlist: tuple = (),
        level: int = 0,
    ) -> Any:
        """Custom import function that defers imports instead of executing them"""
        if not self.active:
            if self.original_import is None:
                raise RuntimeError("Internal error: original_import is None")
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
            frame_info = inspect.getframeinfo(caller_frame)
            if not frame_info.code_context:
                raise RuntimeError(
                    f"Cannot determine import statement for '{name}' - no code context available"
                )
            line = frame_info.code_context[0].strip()

            for deferred_kwargs in self._parse_import_line(line, name):
                deferred = DeferredImport(
                    target_globals=target_globals, **deferred_kwargs
                )
                self.deferred_imports.append(deferred)

        except Exception as e:
            # If we can't parse the import properly, this is a serious problem
            # for aliases, so raise an error
            raise RuntimeError(f"Failed to parse import statement for '{name}'") from e

        dummy_module = DummyObject(name)
        return dummy_module

    def _parse_import_line(self, line: str, name: str):
        """Parse the import line and return kwargs for DeferredImport"""
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
        """Execute a single deferred import"""
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
                module = self.original_import(deferred.module_name, target_globals)
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
        """Check if a package is installed in the system.

        Args:
            package_name: The name of the package as installed (e.g. 'requests', 'django')
                         Same name used with 'pip install package_name'

        Returns:
            True if the package is installed and can be imported, False otherwise

        Example:
            defer.is_installed("requests")  # True if requests is installed
            defer.is_installed("nonexistent")  # False
        """
        spec = find_spec(package_name)
        return spec is not None


class DummyObject:
    """A dummy object that raises an error when called or used"""

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
