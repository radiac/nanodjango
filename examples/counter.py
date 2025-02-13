"""
nanodjango - Django models, views and admin in a single file

Counter example

Usage::

    nanodjango run counter.py
"""

import pytest
from django.db import models

from nanodjango import Django


app = Django(
    # Avoid clashes with other examples
    SQLITE_DATABASE="counter.sqlite3",
    MIGRATIONS_DIR="counter_migrations",
)


@app.admin(list_display=["id", "timestamp"], readonly_fields=["timestamp"])
class CountLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)


@app.route("/")
def count(request):
    CountLog.objects.create()

    return f"<p>Number of page loads: {CountLog.objects.count()}</p>"


@app.api.get("/add")
def add(request):
    # Django Ninja API
    CountLog.objects.create()
    return {"count": CountLog.objects.count()}


###############################################################################
pytestmark = pytest.mark.django_db


parametrized_make_count_log = pytest.mark.parametrize(
    "make_data, expected_count",
    [
        (lambda: None, 1),
        (lambda: CountLog.objects.create(), 2),
    ],
)


@pytest.fixture(scope="module", autouse=True)
def _init():
    """
    Initialize the Django instance (i.e. admin, ninja).
    """
    app._prepare()


@parametrized_make_count_log
def test_index_view(client, expected_count, make_data):
    make_data()
    response = client.get("/")
    assert response.status_code == 200

    result = response.content.decode()
    expected = f"<p>Number of page loads: {expected_count}</p>"
    assert result == expected


@parametrized_make_count_log
def test_api_view(client, expected_count, make_data):
    make_data()
    response = client.get("/api/add")
    assert response.status_code == 200

    result = response.json()
    expected = {"count": expected_count}
    assert result == expected
