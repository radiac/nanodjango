import urllib.request

from .utils import cmd, converted_process, runserver

TEST_APP = "scale"
TEST_SCRIPT = f"examples/{TEST_APP}.py"
TEST_BIND = "127.0.0.1:8042"


def test_runserver__fbv_with_model(tmp_path):
    cmd("run", TEST_SCRIPT, "makemigrations", TEST_APP)
    cmd("run", TEST_SCRIPT, "migrate")
    cmd("convert", TEST_SCRIPT, str(tmp_path), "--name=converted", "--delete")

    with (
        converted_process(tmp_path, "runserver", TEST_BIND) as handle,
        runserver(handle),
    ):
        response = urllib.request.urlopen(f"http://{TEST_BIND}/", timeout=10)
        assert response.getcode() == 200

        response = urllib.request.urlopen(f"http://{TEST_BIND}/count/", timeout=10)
        assert response.getcode() == 200
        assert "Number of page loads" in response.read().decode("utf-8")
