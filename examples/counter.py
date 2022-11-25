from django.db import models

from django_flasky import Django


app = Django()


class CountLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)


@app.route("/")
def count(request):
    CountLog.objects.create()

    return f"<p>Number of page loads: {CountLog.objects.count()}</p>"
