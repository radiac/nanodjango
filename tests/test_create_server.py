import asyncio
import tempfile
import urllib.request
from pathlib import Path

from nanodjango.constants import SQLITE_MEMORY
from nanodjango.testing.utils import run_app_code

TEST_BIND = "127.0.0.1:8043"


def test_create_server__basic():
    """Test that create_server works with host:port format and runs prestart"""
    code = f"""
import asyncio
from nanodjango import Django

app = Django(
    SQLITE_DATABASE="{SQLITE_MEMORY}",
)

@app.route("/")
async def index(request):
    return "<p>Hello from async server</p>"

async def main():
    # Create server with host:port string
    server_task = asyncio.create_task(app.create_server("{TEST_BIND}"))

    # Give server time to start
    await asyncio.sleep(2)

    # Cancel the server
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass

    print("SERVER_STARTED_OK")

if __name__ == "__main__":
    asyncio.run(main())
"""

    result = run_app_code(code, timeout=10)

    # Check that the server started successfully
    # Note: cancelling uvicorn causes SystemExit(1), so we check output not return code
    assert (
        "SERVER_STARTED_OK" in result.stdout
    ), f"stdout: {result.stdout}\nstderr: {result.stderr}"
    # Check that migrations ran (part of _prestart) - output is in stdout
    assert "makemigrations" in result.stdout or "No changes detected" in result.stdout


def test_create_server__serves_requests():
    """Test that create_server actually serves HTTP requests"""
    import os
    import subprocess
    import sys
    import time

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create the app file
        app_file = tmp_path / "test_async_app.py"
        app_file.write_text(f"""
import asyncio
from nanodjango import Django

app = Django(
    SQLITE_DATABASE="{SQLITE_MEMORY}",
)

@app.route("/")
async def index(request):
    return "<p>Hello from async server</p>"

@app.route("/test/")
async def test_view(request):
    return "<p>Test view works</p>"

async def main():
    await app.create_server("{TEST_BIND}")

if __name__ == "__main__":
    asyncio.run(main())
""")

        # Start the server in a subprocess
        # Use proper env setup like _get_nanodjango_env()
        env = os.environ.copy()
        env.pop("DJANGO_SETTINGS_MODULE", None)
        pythonpaths = env.get("PYTHONPATH", "").split(os.pathsep)
        if "." not in pythonpaths:
            pythonpaths.append(".")
        env["PYTHONPATH"] = os.pathsep.join(
            [
                os.path.abspath(p) if p and not os.path.isabs(p) else p
                for p in pythonpaths
                if p
            ]
        )

        process = subprocess.Popen(
            [sys.executable, str(app_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(tmp_path),
            env=env,
        )

        try:
            # Wait for server to start (look for uvicorn started message)
            started = False
            for _ in range(50):  # Try for up to 5 seconds
                time.sleep(0.1)
                if process.poll() is not None:
                    # Process died
                    stdout, stderr = process.communicate()
                    raise AssertionError(
                        f"Server process died unexpectedly:\nstdout: {stdout}\nstderr: {stderr}"
                    )

                # Try to connect
                try:
                    response = urllib.request.urlopen(f"http://{TEST_BIND}/", timeout=1)
                    started = True
                    break
                except Exception:
                    continue

            if not started:
                stdout, stderr = process.communicate(timeout=1)
                raise AssertionError(
                    f"Server didn't start in time:\nstdout: {stdout}\nstderr: {stderr}"
                )

            # Test that the server is responding
            response = urllib.request.urlopen(f"http://{TEST_BIND}/", timeout=5)
            assert response.getcode() == 200
            body = response.read().decode("utf-8")
            assert "Hello from async server" in body

            # Test another route
            response = urllib.request.urlopen(f"http://{TEST_BIND}/test/", timeout=5)
            assert response.getcode() == 200
            body = response.read().decode("utf-8")
            assert "Test view works" in body

        finally:
            process.terminate()
            process.wait(timeout=5)


def test_create_server__with_credentials():
    """Test that create_server creates a superuser with provided credentials"""
    code = f"""
import asyncio
from nanodjango import Django

app = Django(
    SQLITE_DATABASE="{{SQLITE_MEMORY}}",
)

@app.route("/")
async def index(request):
    return "<p>Hello</p>"

async def main():
    # Create server with explicit credentials
    server_task = asyncio.create_task(
        app.create_server("{TEST_BIND.replace('8043', '8044')}", username="testuser", password="testpass123")
    )

    # Give server time to start
    await asyncio.sleep(2)

    # Cancel the server
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass

    print("SERVER_STARTED_OK")

if __name__ == "__main__":
    asyncio.run(main())
"""

    result = run_app_code(code, timeout=10)

    # Note: cancelling uvicorn causes SystemExit(1), so we check output not return code
    assert (
        "SERVER_STARTED_OK" in result.stdout
    ), f"stdout: {result.stdout}\nstderr: {result.stderr}"
    # Check that superuser was created with provided credentials
    assert "testuser" in result.stdout
