"""
nanodjango - Django models, views and admin in a single file

Counter example

Usage::

    nanodjango run counter.py
"""

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
