"""
nanodjango - Django models, views and admin in a single file

A example app using django-ninja to provide an API

    nanodjango ninja-api.py run

See it working at http://localhost:8000/api/add?a=1&b=2
"""

from django.db import models

from nanodjango import Django


app = Django()

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
