===================
Management commands
===================

The ``nanodjango`` command provides a convenient way to run Django management
commands on your app::

    nanodjango <script.py> run [<command>]


If the management command is left out, it will default to ``runserver 0:8000`` - these
two commands are equivalent:

.. code-block:: bash

    nanodjango counter.py run
    nanodjango counter.py run runserver 0:8000


You can run any management command:

.. code-block:: bash

    nanodjango counter.py run migrate


For commands which need to know the name of the app, such as ``makemigrations``,
nanodjango uses the filename as the app name - eg:

.. code-block:: bash

    nanodjango counter.py run makemigrations counter
