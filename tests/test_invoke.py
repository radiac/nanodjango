import os
import subprocess
import sys
from pathlib import Path

from nanodjango.testing.utils import cmd

SCRIPT = Path(__file__).parent.parent / "examples" / "invoke_script.py"


def test_invoke__default():
    # Run the script directly, as uv run would
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=60,
        env={**os.environ, "PYTHONPATH": str(SCRIPT.parent.parent)},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."


def test_invoke__manage_command():
    result = cmd("manage", str(SCRIPT), "check")
    assert result.stdout.strip() == "System check identified no issues (0 silenced)."
