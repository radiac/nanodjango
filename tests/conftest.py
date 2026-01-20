from django.test import Client

import pytest

from nanodjango import Django


@pytest.fixture(scope="session")
def nanodjango_app():
    app = Django()

    # No parameters
    @app.route("/")
    def view(request):
        return "Hello"

    # path() parameters
    @app.route("/<int:pk>/")
    def view(request, pk):  # noqa: F811
        return f"Hello {pk}"

    # re_path() parameters
    @app.route("/(?P<slug>[a-z])/", re=True)
    def view(request, slug):  # noqa: F811
        return f"Hello {slug}"

    return app


@pytest.fixture(scope="module")
def client(nanodjango_app):
    return Client()
