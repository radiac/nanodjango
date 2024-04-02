"""
Django-flasky - Django models, views and admin in a single file

Counter example

Usage::

    django-flasky counter.py run migrate
    django_flasky counter.py run createsuperuser
    django-flasky counter.py run
"""

from django.db import models
from django_flasky import Django

app = Django(ADMIN_URL="admin/")


@app.admin(list_display=["id", "timestamp"], readonly_fields=["timestamp"])
class CountLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)


@app.route("/")
def count(request):
    CountLog.objects.create()

    return f"<p>Number of page loads: {CountLog.objects.count()}</p>"
