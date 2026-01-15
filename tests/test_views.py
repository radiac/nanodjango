import json
from io import BytesIO

from django.http import FileResponse, HttpResponse, JsonResponse, StreamingHttpResponse


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


def test_streaming_response(nanodjango_app, client):
    """Test that StreamingHttpResponse works with @app.route decorator"""

    def event_generator():
        for i in range(3):
            yield f"data: {json.dumps({'count': i})}\n\n".encode("utf-8")

    @nanodjango_app.route("/stream")
    def stream_view(request):
        return StreamingHttpResponse(
            event_generator(), content_type="text/event-stream"
        )

    response = client.get("/stream")
    assert response.status_code == 200
    assert response["Content-Type"] == "text/event-stream"
    assert response.streaming

    # Collect all chunks
    content = b"".join(response.streaming_content)
    assert b"data: " in content
    assert b'"count": 0' in content
    assert b'"count": 1' in content
    assert b'"count": 2' in content


def test_http_response_unchanged(nanodjango_app, client):
    """Test that regular HttpResponse still works"""

    @nanodjango_app.route("/http-response")
    def http_view(request):
        return HttpResponse("Direct HttpResponse", content_type="text/plain")

    response = client.get("/http-response")
    assert response.status_code == 200
    assert response.content == b"Direct HttpResponse"
    assert response["Content-Type"] == "text/plain"


def test_json_response_unchanged(nanodjango_app, client):
    """Test that JsonResponse still works"""

    @nanodjango_app.route("/json-response")
    def json_view(request):
        return JsonResponse({"message": "test"})

    response = client.get("/json-response")
    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"
    data = json.loads(response.content)
    assert data["message"] == "test"


def test_string_conversion_still_works(nanodjango_app, client):
    """Test that string return values are still converted to HttpResponse"""

    @nanodjango_app.route("/string-return")
    def string_view(request):
        return "Plain string"

    response = client.get("/string-return")
    assert response.status_code == 200
    assert response.content == b"Plain string"


def test_file_response(nanodjango_app, client):
    """Test that FileResponse works with @app.route decorator"""

    @nanodjango_app.route("/file")
    def file_view(request):
        file_content = b"This is file content"
        file_obj = BytesIO(file_content)
        return FileResponse(file_obj, content_type="text/plain", as_attachment=False)

    response = client.get("/file")
    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain"
    # FileResponse is a StreamingHttpResponse
    assert response.streaming
    content = b"".join(response.streaming_content)
    assert content == b"This is file content"
