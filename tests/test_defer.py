"""Tests for nanodjango.defer module"""

import builtins

import pytest

from nanodjango.defer import (
    DeferredAttributeError,
    DeferredImport,
    DeferredImportError,
    DeferredModuleNotFoundError,
    DeferredUsageError,
    DummyObject,
    ImportDeferrer,
    defer,
)


class TestDeferredImport:
    """Test the DeferredImport class"""

    def test_repr_simple_import(self):
        """Test __repr__ for simple import"""
        target_globals = {}
        deferred = DeferredImport("os", target_globals)
        assert repr(deferred) == "import os"

    def test_repr_import_with_alias(self):
        """Test __repr__ for import with alias"""
        target_globals = {}
        deferred = DeferredImport("os", target_globals, alias="operating_system")
        assert repr(deferred) == "import os as operating_system"

    def test_repr_from_import(self):
        """Test __repr__ for from import"""
        target_globals = {}
        deferred = DeferredImport("os", target_globals, from_name="path")
        assert repr(deferred) == "from os import path"

    def test_repr_from_import_with_alias(self):
        """Test __repr__ for from import with alias"""
        target_globals = {}
        deferred = DeferredImport(
            "os", target_globals, from_name="path", from_alias="p"
        )
        assert repr(deferred) == "from os import path as p"

    def test_repr_optional(self):
        """Test __repr__ for optional import"""
        target_globals = {}
        deferred = DeferredImport("nonexistent", target_globals, optional=True)
        assert repr(deferred) == "import nonexistent (optional)"

    def test_original_stack_captured(self):
        """Test that original stack trace is captured"""
        target_globals = {}
        deferred = DeferredImport("os", target_globals)
        assert len(deferred.original_stack) > 0
        # Stack should be non-empty (exact content depends on call stack)
        assert isinstance(deferred.original_stack, list)


class TestDummyObject:
    """Test the DummyObject class"""

    def test_attribute_access(self):
        """Test that attribute access returns nested DummyObject"""
        dummy = DummyObject("test_module")
        nested = dummy.some_attr
        assert isinstance(nested, DummyObject)
        assert nested.name == "test_module.some_attr"

    def test_nested_attribute_access(self):
        """Test deeply nested attribute access"""
        dummy = DummyObject("test_module")
        nested = dummy.some.deep.attr
        assert isinstance(nested, DummyObject)
        assert nested.name == "test_module.some.deep.attr"

    def test_call_raises_error(self):
        """Test that calling dummy object raises error"""
        dummy = DummyObject("test_module")
        with pytest.raises(
            DeferredUsageError, match="Cannot use deferred import 'test_module'"
        ):
            dummy()

    def test_str_raises_error(self):
        """Test that str() raises error"""
        dummy = DummyObject("test_module")
        with pytest.raises(
            DeferredUsageError, match="Cannot use deferred import 'test_module'"
        ):
            str(dummy)

    def test_repr_raises_error(self):
        """Test that repr() raises error"""
        dummy = DummyObject("test_module")
        with pytest.raises(
            DeferredUsageError, match="Cannot use deferred import 'test_module'"
        ):
            repr(dummy)

    def test_bool_raises_error(self):
        """Test that bool() raises error"""
        dummy = DummyObject("test_module")
        with pytest.raises(
            DeferredUsageError, match="Cannot use deferred import 'test_module'"
        ):
            bool(dummy)


class TestImportDeferrer:
    """Test the ImportDeferrer class"""

    def test_init(self):
        """Test initialization"""
        deferrer = ImportDeferrer()
        assert not deferrer.active
        assert deferrer.deferred_imports == []
        assert deferrer.original_import is None
        assert deferrer.caller_globals is None
        assert not deferrer._optional_mode
        assert deferrer.file_cache == {}

    def test_context_manager_activation(self):
        """Test context manager activates and deactivates"""
        deferrer = ImportDeferrer()
        assert not deferrer.active

        with deferrer:
            assert deferrer.active

        assert not deferrer.active

    def test_nested_context_manager(self):
        """Test nested context manager behavior"""
        deferrer = ImportDeferrer()

        with deferrer:
            assert deferrer.active
            with deferrer:  # Nested entry doesn't change state
                assert deferrer.active
            # Nested exit deactivates the deferrer
            assert not deferrer.active

        assert not deferrer.active

    def test_import_interception(self):
        """Test that imports are intercepted when active"""
        deferrer = ImportDeferrer()

        with deferrer:
            # This should be intercepted and create a dummy
            import os

            assert isinstance(os, DummyObject)
            assert os.name == "os"

        # Should have one deferred import
        assert len(deferrer.deferred_imports) == 1
        assert deferrer.deferred_imports[0].module_name == "os"

    def test_import_with_alias(self):
        """Test import with alias is handled correctly"""
        deferrer = ImportDeferrer()

        with deferrer:
            import os as operating_system

            assert isinstance(operating_system, DummyObject)
            assert operating_system.name == "os"

        deferred = deferrer.deferred_imports[0]
        assert deferred.module_name == "os"
        assert deferred.alias == "operating_system"

    def test_from_import(self):
        """Test from import is handled correctly"""
        deferrer = ImportDeferrer()

        with deferrer:
            from os import path

            assert isinstance(path, DummyObject)

        deferred = deferrer.deferred_imports[0]
        assert deferred.module_name == "os"
        assert deferred.from_name == "path"

    def test_from_import_with_alias(self):
        """Test from import with alias"""
        deferrer = ImportDeferrer()

        with deferrer:
            from os import path as p

            assert isinstance(p, DummyObject)

        deferred = deferrer.deferred_imports[0]
        assert deferred.module_name == "os"
        assert deferred.from_name == "path"
        assert deferred.from_alias == "p"

    def test_apply_simple_import(self):
        """Test applying simple import"""
        deferrer = ImportDeferrer()
        test_globals = {}

        with deferrer:
            # Manually create a deferred import since we can't easily test globals injection
            deferred = DeferredImport("os", test_globals)
            deferrer.deferred_imports = [deferred]

        deferrer.apply()

        # Should have imported os into test_globals
        assert "os" in test_globals
        assert hasattr(test_globals["os"], "path")  # os module should be real

    def test_apply_import_with_alias(self):
        """Test applying import with alias"""
        deferrer = ImportDeferrer()
        test_globals = {}

        with deferrer:
            deferred = DeferredImport("os", test_globals, alias="operating_system")
            deferrer.deferred_imports = [deferred]

        deferrer.apply()

        assert "operating_system" in test_globals
        assert hasattr(test_globals["operating_system"], "path")

    def test_apply_from_import(self):
        """Test applying from import"""
        deferrer = ImportDeferrer()
        test_globals = {}

        with deferrer:
            deferred = DeferredImport("os", test_globals, from_name="path")
            deferrer.deferred_imports = [deferred]

        deferrer.apply()

        assert "path" in test_globals
        assert hasattr(test_globals["path"], "join")  # os.path should be real

    def test_apply_from_import_with_alias(self):
        """Test applying from import with alias"""
        deferrer = ImportDeferrer()
        test_globals = {}

        with deferrer:
            deferred = DeferredImport(
                "os", test_globals, from_name="path", from_alias="p"
            )
            deferrer.deferred_imports = [deferred]

        deferrer.apply()

        assert "p" in test_globals
        assert hasattr(test_globals["p"], "join")

    def test_apply_while_active_raises_error(self):
        """Test that applying while still active raises error"""
        deferrer = ImportDeferrer()

        with deferrer:
            with pytest.raises(
                RuntimeError, match="Cannot apply imports while still deferring"
            ):
                deferrer.apply()

    def test_optional_context_manager(self):
        """Test optional context manager"""
        deferrer = ImportDeferrer()
        test_globals = {}

        with deferrer.optional:
            deferred = DeferredImport("nonexistent_module", test_globals, optional=True)
            deferrer.deferred_imports = [deferred]

        # Should not raise error when applying optional import that doesn't exist
        deferrer.apply()
        assert test_globals.get("nonexistent_module") is None

    def test_optional_nested_in_regular(self):
        """Test optional context manager nested in regular deferrer"""
        deferrer = ImportDeferrer()
        test_globals = {}

        with deferrer:
            with deferrer.optional:
                deferred = DeferredImport(
                    "nonexistent_module", test_globals, optional=True
                )
                deferrer.deferred_imports = [deferred]

        deferrer.apply()
        assert test_globals.get("nonexistent_module") is None

    def test_nonexistent_module_raises_error(self):
        """Test that nonexistent module raises appropriate error"""
        deferrer = ImportDeferrer()
        test_globals = {}

        with deferrer:
            deferred = DeferredImport("nonexistent_module_12345", test_globals)
            deferrer.deferred_imports = [deferred]

        with pytest.raises(DeferredModuleNotFoundError):
            deferrer.apply()

    def test_nonexistent_attribute_raises_error(self):
        """Test that nonexistent attribute raises appropriate error"""
        deferrer = ImportDeferrer()
        test_globals = {}

        with deferrer:
            deferred = DeferredImport("os", test_globals, from_name="nonexistent_attr")
            deferrer.deferred_imports = [deferred]

        with pytest.raises(DeferredAttributeError):
            deferrer.apply()

    def test_is_installed(self):
        """Test is_installed class method"""
        # Test with standard library module
        assert ImportDeferrer.is_installed("os")
        assert ImportDeferrer.is_installed("sys")

        # Test with nonexistent module
        assert not ImportDeferrer.is_installed("nonexistent_module_12345")

    def test_clear_after_apply(self):
        """Test that deferred imports are cleared after apply"""
        deferrer = ImportDeferrer()
        test_globals = {}

        with deferrer:
            deferred = DeferredImport("os", test_globals)
            deferrer.deferred_imports = [deferred]

        assert len(deferrer.deferred_imports) == 1
        deferrer.apply()
        assert len(deferrer.deferred_imports) == 0
        assert deferrer.caller_globals is None
        assert deferrer.file_cache == {}


class TestDeferredErrors:
    """Test deferred error classes"""

    def test_deferred_import_error(self):
        """Test DeferredImportError includes location info"""
        target_globals = {}
        deferred = DeferredImport("nonexistent", target_globals)
        original_error = ImportError("No module named 'nonexistent'")

        error = DeferredImportError(original_error, deferred)
        assert "No module named 'nonexistent'" in str(error)
        assert error.original_error is original_error
        assert error.deferred is deferred

    def test_deferred_module_not_found_error(self):
        """Test DeferredModuleNotFoundError"""
        target_globals = {}
        deferred = DeferredImport("nonexistent", target_globals)
        original_error = ModuleNotFoundError("No module named 'nonexistent'")

        error = DeferredModuleNotFoundError(original_error, deferred)
        assert isinstance(error, ModuleNotFoundError)
        assert error.original_error is original_error

    def test_deferred_attribute_error(self):
        """Test DeferredAttributeError"""
        target_globals = {}
        deferred = DeferredImport("os", target_globals, from_name="nonexistent")
        original_error = AttributeError("module 'os' has no attribute 'nonexistent'")

        error = DeferredAttributeError(original_error, deferred)
        assert isinstance(error, AttributeError)
        assert error.original_error is original_error


class TestGlobalDeferInstance:
    """Test the global defer instance"""

    def test_global_defer_exists(self):
        """Test that global defer instance exists and is ImportDeferrer"""
        assert isinstance(defer, ImportDeferrer)

    def test_global_defer_context_manager(self):
        """Test using global defer as context manager"""
        # Save original state
        original_active = defer.active
        original_imports = defer.deferred_imports.copy()

        try:
            with defer:
                assert defer.active
                # Do a simple import to test interception
                import json

                assert isinstance(json, DummyObject)

            assert not defer.active
            # Should have captured the import
            assert any(d.module_name == "json" for d in defer.deferred_imports)

        finally:
            # Restore original state
            defer.active = original_active
            defer.deferred_imports = original_imports

    def test_global_defer_optional(self):
        """Test using global defer with optional"""
        original_imports = defer.deferred_imports.copy()

        try:
            with defer.optional:
                # Test that we're in optional mode by checking internal state
                assert defer._optional_mode

            assert not defer._optional_mode

        finally:
            defer.deferred_imports = original_imports


class TestParseImportLine:
    """Test the _parse_import_line method"""

    def test_parse_simple_import(self):
        """Test parsing simple import statement"""
        deferrer = ImportDeferrer()
        line = "import os"

        results = list(deferrer._parse_import_line(line, "os"))
        assert len(results) == 1
        assert results[0] == {
            "module_name": "os",
            "alias": None,
            "optional": False,
        }

    def test_parse_import_with_alias(self):
        """Test parsing import with alias"""
        deferrer = ImportDeferrer()
        line = "import os as operating_system"

        results = list(deferrer._parse_import_line(line, "os"))
        assert len(results) == 1
        assert results[0] == {
            "module_name": "os",
            "alias": "operating_system",
            "optional": False,
        }

    def test_parse_from_import(self):
        """Test parsing from import"""
        deferrer = ImportDeferrer()
        line = "from os import path"

        results = list(deferrer._parse_import_line(line, "os"))
        assert len(results) == 1
        assert results[0] == {
            "module_name": "os",
            "from_name": "path",
            "from_alias": None,
            "optional": False,
        }

    def test_parse_from_import_with_alias(self):
        """Test parsing from import with alias"""
        deferrer = ImportDeferrer()
        line = "from os import path as p"

        results = list(deferrer._parse_import_line(line, "os"))
        assert len(results) == 1
        assert results[0] == {
            "module_name": "os",
            "from_name": "path",
            "from_alias": "p",
            "optional": False,
        }

    def test_parse_multiple_imports(self):
        """Test parsing multiple imports in one line"""
        deferrer = ImportDeferrer()
        line = "import os, sys"

        results = list(deferrer._parse_import_line(line, "os"))
        assert len(results) == 2

        # Should handle both modules
        module_names = [r["module_name"] for r in results]
        assert "os" in module_names
        assert "sys" in module_names

    def test_parse_multiple_from_imports(self):
        """Test parsing multiple from imports"""
        deferrer = ImportDeferrer()
        line = "from os import path, environ"

        results = list(deferrer._parse_import_line(line, "os"))
        assert len(results) == 2

        from_names = [r["from_name"] for r in results]
        assert "path" in from_names
        assert "environ" in from_names

    def test_parse_optional_mode(self):
        """Test parsing in optional mode"""
        deferrer = ImportDeferrer()
        deferrer._optional_mode = True
        line = "import os"

        results = list(deferrer._parse_import_line(line, "os"))
        assert len(results) == 1
        assert results[0]["optional"] is True


class TestIntegration:
    """Integration tests for the defer system"""

    def test_full_workflow(self):
        """Test complete defer workflow"""
        test_globals = {}
        deferrer = ImportDeferrer()

        # Save and replace the globals for this test
        original_builtins_import = builtins.__import__

        try:
            with deferrer:
                # Manually add deferred imports since we can't easily test real interception
                deferred1 = DeferredImport("os", test_globals)
                deferred2 = DeferredImport("sys", test_globals, alias="system")
                deferred3 = DeferredImport(
                    "os", test_globals, from_name="path", from_alias="ospath"
                )

                deferrer.deferred_imports = [deferred1, deferred2, deferred3]

            # Apply all deferred imports
            deferrer.apply()

            # Check that all imports were applied correctly
            assert "os" in test_globals
            assert "system" in test_globals  # sys as system
            assert "ospath" in test_globals  # os.path as ospath

            # Verify they're real objects
            assert hasattr(test_globals["os"], "path")
            assert hasattr(test_globals["system"], "version")
            assert hasattr(test_globals["ospath"], "join")

        finally:
            # Restore original import
            builtins.__import__ = original_builtins_import

    def test_error_propagation(self):
        """Test that errors are properly propagated with context"""
        test_globals = {}
        deferrer = ImportDeferrer()

        with deferrer:
            deferred = DeferredImport("nonexistent_module_xyz", test_globals)
            deferrer.deferred_imports = [deferred]

        with pytest.raises(DeferredModuleNotFoundError) as exc_info:
            deferrer.apply()

        # Check that the error contains useful information
        error = exc_info.value
        assert isinstance(error.original_error, ModuleNotFoundError)
        assert error.deferred.module_name == "nonexistent_module_xyz"

    def test_mixed_optional_and_required(self):
        """Test mixing optional and required imports"""
        test_globals = {}
        deferrer = ImportDeferrer()

        with deferrer:
            # Required import that exists
            deferred1 = DeferredImport("os", test_globals)
            # Optional import that doesn't exist
            deferred2 = DeferredImport(
                "nonexistent_optional", test_globals, optional=True
            )
            # Required import that exists
            deferred3 = DeferredImport("sys", test_globals)

            deferrer.deferred_imports = [deferred1, deferred2, deferred3]

        # Should apply successfully
        deferrer.apply()

        # Required imports should be present
        assert "os" in test_globals
        assert "sys" in test_globals
        # Optional import that failed should be None
        assert test_globals.get("nonexistent_optional") is None
