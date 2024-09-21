===============
Run your script
===============

Run using nanodjango
====================

Nanodjango provides two commands to run your script, which will make and apply
migrations, and ensure you have a superuser.


Development mode
-----------------

To run your script locally, use development mode:

.. code-block:: bash

    nanodjango start script.py [host:port]

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
        app.start()

You can then run the script directly to launch the Django development server. This will
also automatically collect any arguments you may have passed on the command line::

    python hello.py runserver 0:8000


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
        app.start()

This will allow you to pass it to ``uv run`` or ``pipx run``, to run your development
server without installing anything first:

.. code-block:: bash

    # Create a temporary venv with ``nanodjango`` installed, then run the script
    uv start ./script.py

    # Call ``run`` and pass some arguments
    pipx run ./script.py -- runserver 0:8000


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


Management commands
===================

The ``nanodjango`` command provides a convenient way to run Django management
commands on your app::

    nanodjango run <script.py> [<command>]


If the management command is left out, it will default to ``runserver 0:8000`` - these
two commands are equivalent:

.. code-block:: bash

    nanodjango run counter.py
    nanodjango run counter.py runserver 0:8000


You can run any management command:

.. code-block:: bash

    nanodjango run counter.py migrate


For commands which need to know the name of the app, such as ``makemigrations``,
nanodjango uses the filename as the app name - eg:

.. code-block:: bash

    nanodjango run counter.py makemigrations counter
