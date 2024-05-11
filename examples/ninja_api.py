"""
nanodjango - Django models, views and admin in a single file

A example app using django-ninja to provide an API

Can be run in any of these ways::

    nanodjango ninja-api.py run
    python ninja-api.py
    pipx run ninja-api.py  # will automatically install dependencies in a temporary venv

See it working at http://localhost:8000/api/add?a=1&b=2
"""
# /// script
# dependencies = ["nanodjango", "django-ninja"]
# ///
# (required for pipx)

from django.db import models

from nanodjango import Django


app = Django(DEBUG=True, ADMIN_URL="admin/")

from ninja import NinjaAPI  # noqa


api = NinjaAPI()


@app.admin
class CountLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)


@api.get("/add")
def add(request):
    CountLog.objects.create()


app.route("api/", include=api.urls)


@app.route("/")
def index(request):
    return f"<p>Number of API calls: {CountLog.objects.count()}</p>"


if __name__ == "__main__":
    app.run()
# (required for ``python ninja-api.py``)
