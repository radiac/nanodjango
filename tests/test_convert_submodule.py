"""
Test for convert handling of submodule imports.

Regression test for https://github.com/radiac/nanodjango/issues/40
"""

import inspect


def test_getsource_module_package_fails():
    """
    Demonstrate the bug: inspect.getsource on a package with empty __init__.py
    either raises OSError or returns empty source (depending on Python version).

    This is the root cause of issue #40 - when 'import urllib.parse' is used,
    'urllib' ends up in the module namespace, and the converter tries to get
    its source, which fails.
    """
    import ast
    import urllib

    # Depending on Python version, this either:
    # - Raises OSError directly (Python 3.11+)
    # - Returns empty/whitespace source (older versions)
    try:
        src = inspect.getsource(urllib)
    except OSError:
        # Python 3.11+ raises OSError for empty __init__.py
        pass
    else:
        # Older versions return empty source, which causes IndexError on body[0]
        assert src.strip() == ""  # Just whitespace
        parsed = ast.parse(src)
        assert len(parsed.body) == 0


def test_converter_handles_submodule_imports(tmp_path):
    """
    Test that convert handles 'import x.y' style imports without crashing.

    Regression test for https://github.com/radiac/nanodjango/issues/40
    """
    from nanodjango.testing.utils import cmd

    # Create a minimal app with a submodule import
    app_file = tmp_path / "submodule_app.py"
    app_file.write_text('''
import urllib.parse
from nanodjango import Django

app = Django()

@app.route("/")
def index(request):
    encoded = urllib.parse.quote("hello world")
    return f"Encoded: {encoded}"
''')

    output_path = tmp_path / "converted"

    # This should not crash with IndexError or OSError
    result = cmd(
        "convert", str(app_file), str(output_path),
        "--name=converted",
        fail_ok=True,
    )

    # The convert may fail for other reasons (missing admin path in newer Django)
    # but it should NOT fail with "could not get source code" or IndexError
    if result.returncode != 0:
        assert "could not get source code" not in result.stderr.lower()
        assert "indexerror" not in result.stderr.lower()
        assert "list index out of range" not in result.stderr.lower()
