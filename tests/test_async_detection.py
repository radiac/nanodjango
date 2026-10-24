import pytest

from nanodjango.testing.utils import run_app_code

APP_CODE = """
from django.http import HttpResponse
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
    ],
)
def test_has_async(setup, expected):
    result = run_app_code(APP_CODE.format(setup=setup), timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected
