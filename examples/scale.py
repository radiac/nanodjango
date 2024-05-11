"""
nanodjango - Django models, views and admin in a single file

A example project which we want to scale using ``convert``

This is the project used to test that convert works as intended, so aims to use all
supported convertible features. As a result this is a good example of when a project
should be converted.

Usage::

    nanodjango scale.py convert /path/to/site --name=myproject
    cd /path/to/site
    ./manage.py runserver 0:8000
"""
# /// script
# dependencies = ["nanodjango"]
# ///

import os

from django.db import models
from django.http import HttpResponseRedirect
from django.urls import include
from django.views.generic import ListView

from nanodjango import Django


domain = "scale.example.com"

app = Django(
    ADMIN_URL="secret-admin/",
    ALLOWED_HOSTS=["localhost", "127.0.0.1", domain],
    SECRET_KEY=os.environ.get("SECRET_KEY", "unset"),
    SQLITE_DATABASE="scale.sqlite3",
    MIGRATIONS_DIR="scale_migrations",
    EXTRA_APPS=["django.contrib.sites", "django.contrib.flatpages"],
)


class CountLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)


@app.admin
class Author(models.Model):
    name = models.CharField(max_length=100)
    birth_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name


BOOK_GENRES = (
    ("fiction", "Fiction"),
    ("bio", "Biography"),
)


@app.admin(list_display=["name"], readonly_fields=["id"])
class Book(models.Model):
    name = models.CharField(max_length=100)
    authors = models.ManyToManyField(Author)
    genre = models.CharField(max_length=100, choices=BOOK_GENRES)


@app.route("/")
def count(request):
    CountLog.objects.create()

    return f"<p>Number of page loads: {CountLog.objects.count()}</p>"


@app.route("/author/")
def redirect(request) -> HttpResponseRedirect:
    return HttpResponseRedirect("https://radiac.net/")


@app.route("/counts/")
class Counts(ListView):
    model = CountLog


# Contrived test of regex url and include
app.route(r"^flatpages-\d+/", re=True, include=include("django.contrib.flatpages.urls"))

# Some unused definitions
CONSTANT = 1


def something(name):
    return os.getenv(name)


if __name__ == "__main__":
    app.run()
