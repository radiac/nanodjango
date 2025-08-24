import urllib.request

from nanodjango.testing.utils import cmd, nanodjango_process, runserver

TEST_APP = "scale"
TEST_SCRIPT = f"../examples/scale/{TEST_APP}.py"
TEST_BIND = "127.0.0.1:8042"


def test_runserver__fbv_with_model():
    cmd("manage", TEST_SCRIPT, "makemigrations", TEST_APP)
    cmd("manage", TEST_SCRIPT, "migrate")

    with (
        nanodjango_process("manage", TEST_SCRIPT, "runserver", TEST_BIND) as handle,
        runserver(handle),
    ):
        response = urllib.request.urlopen(f"http://{TEST_BIND}/", timeout=10)
        assert response.getcode() == 200
        assert "0 books available" in response.read().decode("utf-8")

        response = urllib.request.urlopen(f"http://{TEST_BIND}/count/", timeout=10)
        assert response.getcode() == 200
        assert "Number of page loads" in response.read().decode("utf-8")


def test_manage_flag_passthrough():
    result = cmd("manage", TEST_SCRIPT, "makemigrations", TEST_APP, "--empty")
    assert "migrations" in result.stdout.lower()
