"""
Django-flasky - Django models, views and admin in a single file

A example project which we want to scale using ``convert``

This is the project used to test that convert works as intended, so aims to use all
supported convertible features.

Usage::

    django-flasky counter.py convert /path/to/site
    cp db.sqlite3 /path/to/site
    cd /path/to/site
    ./manage.py runserver 0:8000
"""
import os

from django.db import models
from django_flasky import Django

domain = "scale.example.com"

app = Django(
    ADMIN_URL="secret-admin/",
    ALLOWED_HOSTS=["localhost", domain],
    SECRET_KEY=os.environ.get("SECRET_KEY", "unset"),
    SQLITE_DATABASE="scale.sqlite3",
    MIGRATIONS_DIR="scale_migrations",
    EXTRA_APPS=["django.contrib.humanize"],
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


# Some unused definitions
CONSTANT = 1


def something(name):
    return os.getenv(name)
