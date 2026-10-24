===========================
Testing a nanodjango script
===========================

As you write nanodjango scripts, you'll often want to write tests that:

* check the script actually loads (``manage.py check``, or ``makemigrations`` /
  ``migrate``), and
* run it for real and check it returns the values you expect from its URLs.

Nanodjango uses exactly this pattern to test its own :doc:`example scripts
</get_started>`, and exposes the helpers it uses as ``nanodjango.testing`` so you can
use them in your own project's test suite.

.. important::

    These helpers are for use with ``pytest``


Running a command
=================

The quickest way to test your script is to run a nanodjango command against it.

You can do this using the ``cmd`` helper; for example, we can run the nanodjango
equivalent of ``manage.py check`` and confirm it exits cleanly:


.. code-block:: python

    from nanodjango.testing import cmd


    def test_myscript_check():
        result = cmd("manage", "myscript.py", "check")
        assert result.stderr.strip() == ""
        assert result.stdout.strip() == (
            "System check identified no issues (0 silenced)."
        )

``cmd()`` runs ``python -m nanodjango <script> <args>`` as a subprocess, and calls
``pytest.fail()`` with the captured stdout/stderr if it returns a non-zero exit code.

You can run any nanodjango command with this; the most common will be to make sure your
script's models are migrated (just remember to use a test database):

.. code-block:: python

    cmd("manage", "myscript.py", "makemigrations")
    cmd("manage", "myscript.py", "migrate")


See :ref:`testing-api` for more details.


Running a script and checking its URLs
=======================================

While you could technically call ``cmd("run")``, it would run your nanodjango site
in a blocking subprocess and lock up your test. Instead, we have a pair of helpers:

* ``nanodjango_process`` - context manager to launch a nanodjango process
* ``runserver`` - context manager to handle the initialisation of a
  ``nanodjango_process`` that calls runserver

You can use them like this:

.. code-block:: python

    import urllib.request

    from nanodjango.testing import cmd, nanodjango_process, runserver

    TEST_SCRIPT = "myscript.py"
    TEST_BIND = "127.0.0.1:8042"


    def test_myscript_urls():
        cmd("manage", TEST_SCRIPT, "makemigrations")
        cmd("manage", TEST_SCRIPT, "migrate")

        with (
            nanodjango_process("manage", TEST_SCRIPT, "runserver", TEST_BIND) as handle,
            runserver(handle),
        ):
            response = urllib.request.urlopen(f"http://{TEST_BIND}/", timeout=10)
            assert response.getcode() == 200
            assert "expected content" in response.read().decode("utf-8")

``nanodjango_process()`` starts ``python -m nanodjango <script> <args>`` and yields
its ``subprocess.Popen`` handle, terminating it when the block exits.
``runserver()`` reads the process's startup output to confirm the server actually
came up (rather than crashing) before you start making requests against it - pass
``expect=EXPECT_UVICORN`` or ``expect=EXPECT_GUNICORN`` if your script runs under
those instead of Django's dev server.

Because starting a server is slow, it's usually best to do it once per test module
and reuse it across tests with a fixture:

.. code-block:: python

    import urllib.request

    import pytest
    from nanodjango.testing import cmd, nanodjango_process, runserver

    TEST_SCRIPT = "myscript.py"
    TEST_BIND = "127.0.0.1:8042"


    @pytest.fixture(scope="module")
    def myscript():
        cmd("manage", TEST_SCRIPT, "makemigrations")
        cmd("manage", TEST_SCRIPT, "migrate")
        with (
            nanodjango_process("manage", TEST_SCRIPT, "runserver", TEST_BIND) as handle,
            runserver(handle),
        ):
            yield handle


    def test_index(myscript):
        response = urllib.request.urlopen(f"http://{TEST_BIND}/", timeout=10)
        assert response.getcode() == 200
        assert "expected content" in response.read().decode("utf-8")


    def test_other_url(myscript):
        response = urllib.request.urlopen(f"http://{TEST_BIND}/other/", timeout=10)
        assert response.getcode() == 200


Testing app code without a script on disk
==========================================

If you want to test a specific bit of nanodjango behaviour rather than a whole
example script - for example while writing a plugin, or reproducing an issue -
``run_app_code()`` writes a string of Python to a temporary file and runs it,
without you needing to manage a fixture file yourself:

.. code-block:: python

    from nanodjango.testing import run_app_code


    def test_debug_setting():
        result = run_app_code("""
            from nanodjango import Django
            app = Django()

            @app.route("/")
            def index(request):
                return "Hello"

            from django.conf import settings
            print("DEBUG:", settings.DEBUG)
        """)

        assert result.returncode == 0
        assert "DEBUG: True" in result.stdout


Working directory
==================

By default, ``cmd()`` and ``nanodjango_process()`` run relative to the directory of
the test file that called them, so paths like ``"myscript.py"`` or
``"../examples/myscript.py"`` work the same way they would from the command line.
Pass an explicit ``cwd`` to ``cmd()`` to override this.


.. _testing-api:

API reference
==============

.. autofunction:: nanodjango.testing.cmd

.. autofunction:: nanodjango.testing.nanodjango_process

.. autofunction:: nanodjango.testing.django_process

.. autofunction:: nanodjango.testing.runserver

.. autofunction:: nanodjango.testing.run_app_code
