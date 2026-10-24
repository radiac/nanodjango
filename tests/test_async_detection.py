import pytest

from nanodjango.testing.utils import run_app_code

APP_CODE = """
from django.http import HttpResponse
from django.urls import include, path
from django.views import View
from nanodjango import Django

app = Django()


class AsyncCBV(View):
    async def get(self, request):
        return HttpResponse("async cbv")


class SyncCBV(View):
    def get(self, request):
        return HttpResponse("sync cbv")


{setup}

print(app.has_async)
"""


@pytest.mark.parametrize(
    "setup, expected",
    [
        ('app.path("sync/")(SyncCBV)', "False"),
        ('app.path("async/")(AsyncCBV)', "True"),
        ('app.path("async/")(AsyncCBV.as_view())', "True"),
        # Included urlpatterns already in memory are detected without mark_async()
        ('app.path("api/", include([path("thing/", AsyncCBV.as_view())]))', "True"),
        (
            'app.path("api/", include([path("a/", include([path("thing/", AsyncCBV.as_view())]))]))',
            "True",
        ),
        ('app.path("api/", include([path("thing/", SyncCBV.as_view())]))', "False"),
        ("app.mark_async()", "True"),
    ],
)
def test_has_async(setup, expected):
    result = run_app_code(APP_CODE.format(setup=setup), timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected


@pytest.mark.parametrize(
    "settings, expected",
    [
        ("", "False"),
        ("ASYNC=True", "True"),
    ],
)
def test_has_async__async_setting(settings, expected):
    result = run_app_code(
        f"""
from django.http import HttpResponse
from nanodjango import Django

app = Django({settings})


@app.path("sync/")
def sync_view(request):
    return HttpResponse("sync")


print(app.has_async)
""",
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected
