import urllib.request

from .utils import cmd, nanodjango_process, runserver

TEST_APP = "scale"
TEST_SCRIPT = f"examples/{TEST_APP}.py"
TEST_BIND = "127.0.0.1:8042"


def test_runserver__fbv_with_model():
    cmd("run", TEST_SCRIPT, "makemigrations", TEST_APP)
    cmd("run", TEST_SCRIPT, "migrate")

    with (
        nanodjango_process("run", TEST_SCRIPT, "runserver", TEST_BIND) as handle,
        runserver(handle),
    ):
        response = urllib.request.urlopen(f"http://{TEST_BIND}/", timeout=10)
        assert response.getcode() == 200

        response = urllib.request.urlopen(f"http://{TEST_BIND}/count/", timeout=10)
        assert response.getcode() == 200
        assert "Number of page loads" in response.read().decode("utf-8")
