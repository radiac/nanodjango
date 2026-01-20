"""
Tools for running tests with nanodjango

Recommended usage is through a module-level fixture:

    import urllib.request

    import pytest
    from nanodjango.testing.utils import cmd, nanodjango_process, runserver

    TEST_APP = "myscript"
    TEST_SCRIPT = f"examples/{TEST_APP}.py"
    TEST_BIND = "127.0.0.1:8042"


    @pytest.fixture(scope='module')  # or 'session' for session-wide setup
    def myscript():
        cmd("manage", TEST_SCRIPT, "makemigrations", TEST_APP)
        cmd("manage", TEST_SCRIPT, "migrate")
        with (
            nanodjango_process("manage", TEST_SCRIPT, "runserver", TEST_BIND) as handle,
            runserver(handle),
        ):
            yield handle

    def test_url(myscript):
        response = urllib.request.urlopen(f"http://{TEST_BIND}/", timeout=10)
        assert response.getcode() == 200
        assert "content" in response.read().decode("utf-8")
"""

import inspect
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import django

import pytest

RUNSERVER_TIMEOUT = 10  # seconds
SUBPROCESS_TIMEOUT = 5  # seconds


def _get_caller_cwd() -> Path:
    """
    Find the dir of the file with the function that called into this

    Eg:
    * tests/foo/test_bar.py::foo() calls nanodjango_process()
    * nanodjango_process is wrapped by contextmanager
    * nanodjango_process() calls this
    * this returns Path(tests/foo)
    """
    # Walk the stack
    stack = inspect.stack()
    for frame_info in stack:
        file = frame_info.filename
        frame = frame_info.frame
        module_name = frame.f_globals["__name__"]

        # Ignore this file and contextlib
        if module_name in [__name__, "contextlib"]:
            continue

        # First frame that's not ignored, must be our caller
        break

    return Path(file).parent


def _get_nanodjango_env() -> dict:
    """
    Get a copy of the current env suitable for running nanodjango in a subprocess.

    * remove vars for standard Django tests but which don't make sense for nanodjango
    * ensure the cwd is added to PYTHONPATH - we will normally move the cwd to the test
      dir, but tests are often run in an env where the tested module isn't installed.

    This makes it easier for a project with its own tests to black-box test a nanodjango
    script.
    """
    env = os.environ.copy()

    # Remove vars used for standard Django tests
    env.pop("DJANGO_SETTINGS_MODULE", None)

    # Convert relative paths in PYTHONPATH to absolute paths
    pythonpaths = env.get("PYTHONPATH", "").split(os.pathsep)
    if "." not in pythonpaths:
        pythonpaths.append(".")
    updated_paths = []
    for path in pythonpaths:
        if not path:
            # Skip empty paths
            continue

        if os.path.isabs(path):
            # Keep absolute paths as-is
            updated_paths.append(path)
        else:
            # Resolve relative
            resolved_path = os.path.abspath(path)
            updated_paths.append(resolved_path)

    env["PYTHONPATH"] = os.pathsep.join(updated_paths)

    return env


def cmd(
    script: str,
    *args: str,
    fail_ok: bool = False,
    cwd: Path | str | None = None,
    timeout: float = SUBPROCESS_TIMEOUT,
    **kwargs,
) -> subprocess.CompletedProcess:
    """
    Execute a command, check it was ok, and return the CompletedProcess result

    Args:
        script (str):
            Command to run

        *args (list[str]):
            Arguments for the command

        fail_ok (bool):
            If False, call pytest.fail if subprocess.run returns an error code. If True,
            do not fail. Default: False

        cwd (Path):
            Optional path to current working directory

        timeout (float):
            Timeout in seconds for the subprocess. Default: SUBPROCESS_TIMEOUT

        **kwargs:
            Keyword arguments for subprocess.run

    Returns:
        result (subprocess.CompletedProcess): the result from subprocess.run
    """
    if cwd is None:
        cwd = _get_caller_cwd()
    cmd_list = [sys.executable, "-m", "nanodjango", script, *args]

    # Initialize variables for error reporting
    stdout = ""
    stderr = ""
    error_msg = None
    result = None

    try:
        result = subprocess.run(
            cmd_list,
            env=_get_nanodjango_env(),
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
            **kwargs,
        )
        stdout = result.stdout
        stderr = result.stderr

        if not fail_ok and result.returncode != 0:
            error_msg = (
                "Test subprocess returned a non-zero result when fail_ok is False"
            )

    except subprocess.TimeoutExpired as e:
        stdout = e.stdout or ""
        stderr = e.stderr or ""
        error_msg = f"Test subprocess timed out after {timeout} seconds"

    # Handle any error condition
    if error_msg and not fail_ok:
        pytest.fail(f"""
{error_msg}:

Command
-------
{" ".join(cmd_list)}

stdout
------
{stdout}

stderr
------
{stderr}
""")

    return result


@contextmanager
def nanodjango_process(script: str, *args) -> Generator[subprocess.Popen, None, None]:
    """
    Context manager to run a nanodjango process in a subprocess and collect its Popen
    instance

    Args:
        script (str):
            Command to run

        *args (list[str]):
            Arguments for the command

    Returns:
        process (subprocess.Popen): the subprocess handle
    """
    handle = subprocess.Popen(
        [sys.executable, "-m", "nanodjango", script, *args],
        env=_get_nanodjango_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=_get_caller_cwd(),
    )

    try:
        yield handle
    finally:
        handle.terminate()


@contextmanager
def django_process(path: Path, *args) -> Generator[subprocess.Popen, None, None]:
    """
    Context manager to run a full Django project in a subprocess and collect its Popen
    instance

    Args:
        path (Path):
            Path to Django project

        *args (list[str]):
            Arguments for the command

    Returns:
        process (subprocess.Popen): the subprocess handle
    """
    env = os.environ.copy()
    handle = subprocess.Popen(
        [sys.executable, "manage.py", *args],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=path,
    )

    try:
        yield handle
    finally:
        handle.terminate()


@contextmanager
def runserver(server: subprocess.Popen) -> Generator[subprocess.Popen, None, None]:
    """
    Context manager to read the output header from a ``runserver`` subprocess to check
    it started correctly, and print any failure output to the console.

    Args:
        server (subprocess.Popen):
            The return value from a ``nanodjango_process`` or ``django_process`` call

    Returns:
        server (subprocess.Popen)
            The same argument
    """
    stdout = server.stdout
    stderr = server.stderr
    if not stdout or not stderr:
        pytest.fail(f"Server did not start correctly: {stdout=} {stderr=}")

    # Wait for server to start
    if django.VERSION < (5, 0, 0):
        expecting = "Starting development server at"
    else:
        expecting = "Watching for file changes"
    timeout = time.time() + (RUNSERVER_TIMEOUT * 2)
    out = ""
    os.set_blocking(stdout.fileno(), False)
    os.set_blocking(stderr.fileno(), False)

    while time.time() < timeout:
        out += stdout.readline() + stderr.readline()

        if "Error" in out or expecting in out:
            # Wait long enough for errors or completion
            time.sleep(5)
            out += stdout.readline() + stderr.readline()
            break
        else:
            time.sleep(0.1)

    if "Error" in out or expecting not in out:
        pytest.fail(f"Server did not start correctly: {out}")

    try:
        yield server
    except Exception:
        print("".join([out] + stdout.readlines() + stderr.readlines()))
        raise
