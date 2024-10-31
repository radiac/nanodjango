import pytest
from django.test import Client

from nanodjango import Django


@pytest.fixture(scope="session", autouse=True)
def nanodjango_app():
    app = Django()

    # No parameters
    @app.route("/")
    def view(request):
        return "Hello"

    # path() parameters
    @app.route("/<int:pk>/")
    def view(request, pk):
        return f"Hello {pk}"

    # re_path() parameters
    @app.route("/(?P<slug>[a-z])/", re=True)
    def view(request, slug):
        return f"Hello {slug}"

    return app


@pytest.fixture(scope="module", autouse=True)
def client():
    return Client()


def test_get(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.content == b"Hello"


def test_get_with_param(client):
    response = client.get("/123/")
    assert response.status_code == 200
    assert response.content == b"Hello 123"


def test_get_with_re_param(client):
    response = client.get("/a/")
    assert response.status_code == 200
    assert response.content == b"Hello a"
