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

You can then run the script directly to launch the Django development server:

.. code-block:: bash

    python hello.py
    python hello.py 0:7000


Running it as a standalone script
---------------------------------

You can take it a step further and add a `PEP 723 <https://peps.python.org/pep-0723/>`_
comment to the top to specify ``nanodjango`` as a dependency.

If you're doing this, you may prefer to use ``app.invoke()`` which passes the command
and arguments through to nanodjango's command processor, as if you'd called
``nanodjango <command> myscript.py <args>`` directly:

.. code-block:: python

    # /// script
    # dependencies = ["nanodjango"]
    # ///
    from nanodjango import Django
    app = Django()
    ...
    if __name__ == "__main__":
        app.invoke(default="run 0:3000")

The optional ``app.invoke(default=...)`` argument overrides nanodjango's default
behaviour when no argument is passed - here it will run the dev server on port 3000 if
no args are passed.

This will allow you to pass it to ``uv run`` or ``pipx run``, to run your development
server without installing anything first:

.. code-block:: bash

    # Create a temporary venv with ``nanodjango`` installed
    # No arguments uses the ``default`` if provided - in this case, ``run 0:3000``
    uv run ./script.py

    # Same, but using pipx:
    pipx run ./script.py

    # Run nanodjango commands:
    uv run ./script.py serve 0:5000
    uv run ./script.py manage migrate
    uv run ./script.py manage distill-local output/  # needs django-distill in the deps


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


.. _playground:

Sharing on the Playground
=========================

You can share your nanodjango scripts on the `nanodjango.dev <https://nanodjango.dev>`_
playground. Scripts run live in the browser - anyone with the link can try them out.

You will need to create an account at nanodjango.dev before you can use these commands.


Sharing a script
----------------

Upload a script to the playground:

.. code-block:: bash

    nanodjango share counter.py

This is an alias for ``nanodjango play share``. On success it prints the live URL.

If you already have a script with that name in the playground, pass ``--force`` to
overwrite it:

.. code-block:: bash

    nanodjango share counter.py --force

Options:

``--name=TEXT``
  Script name used in the URL (default: filename stem, eg ``counter``).

``--title=TEXT``
  Human-readable title shown on the playground (default: name).

``--description=TEXT``
  Short description shown on the playground.

``-r / --requirements=PATH``
  Path to a ``requirements.txt``-style file listing extra packages to install.

``--package=TEXT``
  Add a single package to the requirements (repeatable):

  .. code-block:: bash

      nanodjango share counter.py --package requests --package pillow

``--env=TEXT``
  Declare an environment variable the script expects (repeatable). Use
  ``VARNAME`` for a bare declaration, or ``VARNAME:Description`` to include a
  human-readable description shown to users when they run the script:

  .. code-block:: bash

      nanodjango share counter.py --env SECRET_KEY --env "API_URL:Base URL of the upstream API"

  The actual values are entered by each user in their browser and are never
  stored on the server.

``--force``
  Overwrite the script if it already exists.


Pulling a script
----------------

Download a script from the playground:

.. code-block:: bash

    # Pull your script (saves as counter.py)
    nanodjango pull counter

    # Pull your script to another filename
    nanodjango pull counter counter_example.py

    # Pull someone else's script
    nanodjango pull alice/counter

This is an alias for ``nanodjango play pull``. The script is saved to ``{name}.py`` in
the current directory by default.

Options:

``TARGET``
  Optional second argument - path to write the file to (default: ``{name}.py``).

``--force``
  Overwrite the target file if it already exists.


Listing scripts
---------------

List all scripts for the authenticated user:

.. code-block:: bash

    nanodjango play list
    nanodjango play ls

List scripts for another user:

.. code-block:: bash

    nanodjango play list alice


Authentication
--------------

Log in with the device flow (opens a browser tab to approve access):

.. code-block:: bash

    nanodjango play login

Log out and revoke the stored API key:

.. code-block:: bash

    nanodjango play logout

Credentials are stored in ``~/.config/nanodjango/credentials.json``.

``share`` and ``pull`` will trigger the login flow automatically if you are not already
logged in, so you rarely need to run ``login`` explicitly.
