import os
import subprocess
import sys
import time
from contextlib import contextmanager

import django

import pytest


TIMEOUT = 10  # seconds


def cmd(script, *args, fail_ok=False):
    """
    Execute a command and check it was ok (optiona)
    """
    cmd = [sys.executable, "-mnanodjango", script, *args]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(__file__),
        env={"PYTHONPATH": ".."},
    )

    if fail_ok:
        return result
    elif result.returncode != 0:
        pytest.fail(f"{' '.join(cmd)} failed: {result.stdout=} {result.stderr=}")
    return result


@contextmanager
def process(script: str, *args):
    handle = subprocess.Popen(
        [sys.executable, "-mnanodjango", script, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.path.dirname(__file__),
        env={"PYTHONPATH": ".."},
    )

    try:
        yield handle
    finally:
        handle.terminate()


@contextmanager
def runserver(script: str, app: str, bind: str):
    cmd(script, "run", "makemigrations", app)
    cmd(script, "run", "migrate")

    with process(script, "run", "runserver", bind) as server:
        stdout = server.stdout
        stderr = server.stderr
        if not stdout or not stderr:
            pytest.fail(f"Server did not start correctly: {stdout=} {stderr=}")

        # Wait for server to start
        if django.VERSION < (5, 0, 0):
            expecting = "Starting development server at"
        else:
            expecting = "Watching for file changes"
        timeout = time.time() + TIMEOUT
        out = ""
        os.set_blocking(stdout.fileno(), False)
        os.set_blocking(stderr.fileno(), False)

        while time.time() < timeout:
            out += stdout.readline() + stderr.readline()

            if "Error" in out or expecting in out:
                # Wait long enough for errors
                time.sleep(0.5)
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
