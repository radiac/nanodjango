import pytest
from nanodjango import Django

app = Django()


@app.route("/")
def hello_world(request):
    return "<p>Hello, World!</p>"


########################################################################################


@pytest.fixture(scope="module", autouse=True)
def _init():
    """
    Initialize the Django instance (i.e. admin, ninja).
    """
    app._prepare()


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Hello, World" in response.content.decode()
