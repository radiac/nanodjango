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
