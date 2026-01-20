from django.test import Client

import pytest

from nanodjango import Django


def pytest_configure(config):
    """Register custom markers for optional dependency tests."""
    config.addinivalue_line(
        "markers", "requires_extra: mark test as requiring a specific extra"
    )
    config.addinivalue_line("markers", "requires_api: mark test as requiring [api]")
    config.addinivalue_line(
        "markers", "requires_serve: mark test as requiring [serve]"
    )
    config.addinivalue_line(
        "markers", "requires_convert: mark test as requiring [convert]"
    )


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
