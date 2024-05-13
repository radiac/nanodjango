===================
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
        app.run()

This will allow you to pass it to ``pipx run``, to run your development server without
installing anything first:

.. code-block:: bash

    # Create a temporary venv with ``nanodjango`` installed, then run the script
    pipx run ./script.py

    # Pass some arguments
    pipx run ./script.py -- runserver 0:8000


Running in production
---------------------

The commands above are suitable for running the Django development server locally, but
are not appropriate for use in production.

Instead, you can pass nanodjango's ``app = Django()`` to a WSGI server:

.. code-block:: bash

    gunicorn -w 4 counter:app
