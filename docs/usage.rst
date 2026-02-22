=============
Command usage
=============

The ``nanodjango`` shell command has several subcommands.


Run using nanodjango
====================

Nanodjango provides two commands to run your script, which will make and apply
migrations, and ensure you have a superuser.


Development mode
-----------------

To run your script locally, use development mode:

.. code-block:: bash

    nanodjango run script.py [host:port]

This uses ``runserver`` (or ``uvicorn`` for async views), and uses Django's ``static``
to serve static and media files.


Production mode
---------------

If you are deploying your script to a server, run it in production mode:

.. code-block:: bash

    nanodjango serve script.py [host:port]


This uses ``gunicorn`` (or ``uvicorn`` for async views), serving static files using
``whitenoise``.

Static files will be collected into ``settings.STATIC_ROOT`` which is
``static-collected`` by default. Note: this directory will be wiped and recreated each
time you run ``serve``.

This mode does not serve media files; you should put this behind a web server such as
``nginx``, and use that to serve your media files directly.


Root files
----------

In both development and production, nanodjango will also look for a ``PUBLIC_DIR``
(``public`` by default), and if it exists will serve any files at the root (using
``WHITENOISE_ROOT``) - useful for ``favicon.ico``, ``robots.txt`` etc.

Note: ``PUBLIC_DIR`` will be ignored if ``WHITENOISE_ROOT`` is set.


Run and serve options
---------------------

The ``run`` and ``serve`` commands take the following options:

``--user``, ``--user=username`` (or ``--username``) (`experimental <https://github.com/radiac/nanodjango/issues/94>`_):
  When nanodjango runs ``createsuperuser`` it will try to create a superuser.

  If this is provided with a username (eg ``--user=myuser``), it will create a user if
  they don't already exist in the database.

  If specified without a username (eg ``--user``), it will run ``createsuperuser``
  interactively and prompt for a username.

  If not specified, it will use the current system user without prompting.

``--pass``, ``--pass=password`` (or ``--password``) (`experimental <https://github.com/radiac/nanodjango/issues/94>`_):
  When creating a superuser, set the password to the given value.

  If this is provided with a password, it will create a user if they don't already exist
  in the database.

  If specified without a password, it will prompt for a password.

  If not specified, it will generate a random password and print it to the console.

  This option will be ignored if ``--user`` is specified without a username.

  Note: this will not update the password for existing users - to do that, run
  ``nanodjango manage script.py changepassword <username>``

``host:port``:
  Specify the host and port to bind to, eg ``nanodjango run script.py 0.0.0.0:3000``

  Default: ``0.0.0.0:8000``


.. _run_script:

Running your script directly
============================

You don't need to use the ``nanodjango`` command - you can call ``app.run()`` from the
bottom of your script, eg:

.. code-block:: python

    from nanodjango import Django
    app = Django()
    ...
    if __name__ == "__main__":
        app.run()

You can then run the script directly to launch the Django development server::

    python hello.py


Running it as a standalone script
---------------------------------

You can take it a step further and add a `PEP 723 <https://peps.python.org/pep-0723/>`_
comment to the top to specify ``nanodjango`` as a dependency:

.. code-block:: python

    # /// script
    # dependencies = ["nanodjango"]
    # ///
    from nanodjango import Django
    app = Django()
    ...
    if __name__ == "__main__":
        app.run()

This will allow you to pass it to ``uv run`` or ``pipx run``, to run your development
server without installing anything first:

.. code-block:: bash

    # Create a temporary venv with ``nanodjango`` installed, then run the script
    uv run ./script.py

    # Same, but using pipx:
    pipx run ./script.py


Run using WSGI or ASGI
======================

If you prefer to run ``gunicorn`` or ``uvicorn`` directly, you can pass nanodjango's
``app = Django()`` to a WSGI server:

.. code-block:: bash

    gunicorn -w 4 counter:app

or if you have async views, you can use an ASGI server:

.. code-block:: bash

    uvicorn counter:app

Because the WSGI and ASGI handlers are different, the nanodjango ``app`` will offer WSGI
by default, and automatically swap to ASGI if an ``async`` view or API endpoint is
found. If you want to override this behaviour, you can specify the handler:

.. code-block:: bash

    gunicorn counter:app.wsgi
    uvicorn counter:app.asgi


Run as an async task
====================

If you want to run nanodjango alongside other async code in the same process, you can
use ``app.create_server()`` to run it as a task in an existing async event loop:

.. code-block:: python

    async def main():
        await asyncio.gather(
            app.create_server(),
            other_task(),
        )

    if __name__ == "__main__":
        asyncio.run(main())

The ``create_server()`` method accepts the following optional arguments:

``host``:
  Host and port in format ``"host:port"`` (default: ``"0.0.0.0:8000"``)

``username``:
  Username for superuser creation. Pass ``None`` to use system username, ``""`` to
  prompt, or a specific username value.

``password``:
  Password for superuser creation. Pass ``None`` to use ``DJANGO_SUPERUSER_PASSWORD``
  env var or generate random, ``""`` to prompt, or a specific password value.

``log_level``:
  Uvicorn log level (default: ``"info"``)

``is_prod``:
  Whether to run in production mode (default: ``True``)

Note that because it's running async, ``makemigrations`` will be run with the
``--no-input`` option, so may fail if the migration cannot be created without user help.
If this happens, run ``nanodjango manage script.py makemigrations``.


Management commands
===================

The ``nanodjango`` command provides a convenient way to run Django management
commands on your app::

    nanodjango manage <script.py> [<command>]


If the management command is left out, it will default to ``runserver 0.0.0.0:8000`` - these
two commands are equivalent:

.. code-block:: bash

    nanodjango manage counter.py
    nanodjango manage counter.py runserver 0.0.0.0:8000


You can perform any management command:

.. code-block:: bash

    nanodjango manage counter.py migrate


For commands which need to know the name of the app, such as ``makemigrations``,
nanodjango uses the filename as the app name - eg:

.. code-block:: bash

    nanodjango manage counter.py makemigrations counter
