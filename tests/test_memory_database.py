"""
Tests for SQLITE_MEMORY and SQLITE_TMP database support

Verifies migrations run, database writes persist, and servers start correctly
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from nanodjango.constants import SQLITE_MEMORY, SQLITE_TMP
from nanodjango.testing.utils import (
    EXPECT_GUNICORN,
    EXPECT_RUNSERVER,
    EXPECT_UVICORN,
    nanodjango_process,
    runserver,
)

# Sync views app template
SYNC_APP = """
from nanodjango import Django
from django.db import models

app = Django(SQLITE_DATABASE="{db_type}")

class Item(models.Model):
    name = models.CharField(max_length=100)

@app.route("/")
def index(request):
    return f"<p>Items: {{Item.objects.count()}}</p>"

@app.route("/add/")
def add(request):
    Item.objects.create(name="test")
    return f"<p>Added. Items: {{Item.objects.count()}}</p>"

if __name__ == "__main__":
    app.{command}("{bind}")
"""

# Async views app template
ASYNC_APP = """
from nanodjango import Django
from django.db import models

app = Django(SQLITE_DATABASE="{db_type}")

class Item(models.Model):
    name = models.CharField(max_length=100)

@app.route("/")
async def index(request):
    count = await Item.objects.acount()
    return f"<p>Items: {{count}}</p>"

@app.route("/add/")
async def add(request):
    await Item.objects.acreate(name="test")
    count = await Item.objects.acount()
    return f"<p>Added. Items: {{count}}</p>"

if __name__ == "__main__":
    app.{command}("{bind}")
"""


def test_sync_dev_memory():
    """Sync views + runserver + SQLITE_MEMORY"""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_file = Path(tmpdir) / "test_app.py"
        app_file.write_text(
            SYNC_APP.format(db_type=SQLITE_MEMORY, command="run", bind="127.0.0.1:8050")
        )

        with nanodjango_process(
            "run", str(app_file), "127.0.0.1:8050"
        ) as handle, runserver(handle, EXPECT_RUNSERVER):
            response = urllib.request.urlopen("http://127.0.0.1:8050/", timeout=10)
            assert response.getcode() == 200
            assert "Items: 0" in response.read().decode("utf-8")

            response = urllib.request.urlopen("http://127.0.0.1:8050/add/", timeout=10)
            assert "Items: 1" in response.read().decode("utf-8")

            response = urllib.request.urlopen("http://127.0.0.1:8050/", timeout=10)
            assert "Items: 1" in response.read().decode("utf-8")


def test_sync_dev_tmp():
    """Sync views + runserver + SQLITE_TMP"""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_file = Path(tmpdir) / "test_app.py"
        app_file.write_text(
            SYNC_APP.format(db_type=SQLITE_TMP, command="run", bind="127.0.0.1:8051")
        )

        with nanodjango_process(
            "run", str(app_file), "127.0.0.1:8051"
        ) as handle, runserver(handle, EXPECT_RUNSERVER):
            response = urllib.request.urlopen("http://127.0.0.1:8051/", timeout=10)
            assert "Items: 0" in response.read().decode("utf-8")

            response = urllib.request.urlopen("http://127.0.0.1:8051/add/", timeout=10)
            assert "Items: 1" in response.read().decode("utf-8")

            response = urllib.request.urlopen("http://127.0.0.1:8051/", timeout=10)
            assert "Items: 1" in response.read().decode("utf-8")


def test_sync_prod_memory():
    """Sync views + gunicorn + SQLITE_MEMORY - warns about incompatibility"""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_file = Path(tmpdir) / "test_app.py"
        app_file.write_text(
            SYNC_APP.format(
                db_type=SQLITE_MEMORY, command="serve", bind="127.0.0.1:8052"
            )
        )

        with nanodjango_process("serve", str(app_file), "127.0.0.1:8052") as handle:
            # Wait a moment for startup output
            time.sleep(2)

            # Read startup output
            os.set_blocking(handle.stdout.fileno(), False)
            os.set_blocking(handle.stderr.fileno(), False)
            output = handle.stdout.read() + handle.stderr.read()

            # Verify warning is shown
            assert "WARNING" in output
            assert "In-memory database incompatible with gunicorn" in output
            assert "Django.SQLITE_TMP" in output


def test_sync_prod_tmp():
    """Sync views + gunicorn + SQLITE_TMP"""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_file = Path(tmpdir) / "test_app.py"
        app_file.write_text(
            SYNC_APP.format(db_type=SQLITE_TMP, command="serve", bind="127.0.0.1:8053")
        )

        with nanodjango_process(
            "serve", str(app_file), "127.0.0.1:8053"
        ) as handle, runserver(handle, EXPECT_GUNICORN):
            response = urllib.request.urlopen("http://127.0.0.1:8053/", timeout=10)
            assert "Items: 0" in response.read().decode("utf-8")

            response = urllib.request.urlopen("http://127.0.0.1:8053/add/", timeout=10)
            assert "Items: 1" in response.read().decode("utf-8")

            response = urllib.request.urlopen("http://127.0.0.1:8053/", timeout=10)
            assert "Items: 1" in response.read().decode("utf-8")


def test_async_dev_memory():
    """Async views + uvicorn dev (reload disabled) + SQLITE_MEMORY"""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_file = Path(tmpdir) / "test_app.py"
        app_file.write_text(
            ASYNC_APP.format(
                db_type=SQLITE_MEMORY, command="run", bind="127.0.0.1:8054"
            )
        )

        with nanodjango_process(
            "run", str(app_file), "127.0.0.1:8054"
        ) as handle, runserver(handle, EXPECT_UVICORN):
            response = urllib.request.urlopen("http://127.0.0.1:8054/", timeout=10)
            assert "Items: 0" in response.read().decode("utf-8")

            response = urllib.request.urlopen("http://127.0.0.1:8054/add/", timeout=10)
            assert "Items: 1" in response.read().decode("utf-8")

            response = urllib.request.urlopen("http://127.0.0.1:8054/", timeout=10)
            assert "Items: 1" in response.read().decode("utf-8")


def test_async_dev_tmp():
    """Async views + uvicorn dev (reload enabled) + SQLITE_TMP"""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_file = Path(tmpdir) / "test_app.py"
        app_file.write_text(
            ASYNC_APP.format(db_type=SQLITE_TMP, command="run", bind="127.0.0.1:8055")
        )

        with nanodjango_process(
            "run", str(app_file), "127.0.0.1:8055"
        ) as handle, runserver(handle, EXPECT_UVICORN):
            response = urllib.request.urlopen("http://127.0.0.1:8055/", timeout=10)
            assert "Items: 0" in response.read().decode("utf-8")

            response = urllib.request.urlopen("http://127.0.0.1:8055/add/", timeout=10)
            assert "Items: 1" in response.read().decode("utf-8")

            response = urllib.request.urlopen("http://127.0.0.1:8055/", timeout=10)
            assert "Items: 1" in response.read().decode("utf-8")


def test_async_prod_memory():
    """Async views + uvicorn prod + SQLITE_MEMORY"""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_file = Path(tmpdir) / "test_app.py"
        app_file.write_text(
            ASYNC_APP.format(
                db_type=SQLITE_MEMORY, command="serve", bind="127.0.0.1:8056"
            )
        )

        with nanodjango_process(
            "serve", str(app_file), "127.0.0.1:8056"
        ) as handle, runserver(handle, EXPECT_UVICORN):
            response = urllib.request.urlopen("http://127.0.0.1:8056/", timeout=10)
            assert "Items: 0" in response.read().decode("utf-8")

            response = urllib.request.urlopen("http://127.0.0.1:8056/add/", timeout=10)
            assert "Items: 1" in response.read().decode("utf-8")

            response = urllib.request.urlopen("http://127.0.0.1:8056/", timeout=10)
            assert "Items: 1" in response.read().decode("utf-8")


def test_async_prod_tmp():
    """Async views + uvicorn prod + SQLITE_TMP"""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_file = Path(tmpdir) / "test_app.py"
        app_file.write_text(
            ASYNC_APP.format(db_type=SQLITE_TMP, command="serve", bind="127.0.0.1:8057")
        )

        with nanodjango_process(
            "serve", str(app_file), "127.0.0.1:8057"
        ) as handle, runserver(handle, EXPECT_UVICORN):
            response = urllib.request.urlopen("http://127.0.0.1:8057/", timeout=10)
            assert "Items: 0" in response.read().decode("utf-8")

            response = urllib.request.urlopen("http://127.0.0.1:8057/add/", timeout=10)
            assert "Items: 1" in response.read().decode("utf-8")

            response = urllib.request.urlopen("http://127.0.0.1:8057/", timeout=10)
            assert "Items: 1" in response.read().decode("utf-8")
