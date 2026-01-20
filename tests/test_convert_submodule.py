"""
Test for convert handling of submodule imports.

Regression test for https://github.com/radiac/nanodjango/issues/40
"""

import inspect


def test_getsource_empty_module_causes_index_error():
    """
    Demonstrate the bug: inspect.getsource on a package with empty __init__.py
    returns minimal source that causes IndexError when accessing AST body[0].

    This is the root cause of issue #40 - when 'import urllib.parse' is used,
    'urllib' ends up in the module namespace, and the converter tries to get
    its source, which fails.
    """
    import ast
    import urllib

    # This succeeds but returns essentially empty source
    src = inspect.getsource(urllib)
    assert src.strip() == ""  # Just whitespace

    # Parsing empty source gives empty body
    parsed = ast.parse(src)
    assert len(parsed.body) == 0

    # This is where the converter fails - trying to access body[0]
    try:
        _ = parsed.body[0]
        raise AssertionError("Expected IndexError")
    except IndexError:
        pass  # This is the bug we're fixing


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
