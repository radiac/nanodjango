============
Contributing
============

Development
===========

Check out your fork and install its dependencies in a virtualenv:

.. code-block:: bash

    git clone git@github.com:USERNAME/nanodjango.git repo
    python -mvenv venv
    . venv/bin/activate
    cd repo
    pip install -r requirements.txt


Then run examples by adding your ``repo`` dir to the ``PYTHONPATH``, and call
the repo module directly::

    cd examples
    PYTHONPATH=.. python -m nanodjango counter.py run migrate


Tests
=====

To run the tests, still in your virtual environment:

.. code-block:: bash

    cd repo
    pip install -r tests/requirements.txt
    pytest


Thanks
======

Thanks to `Remix Icon <https://remixicon.com/>`_ for the example icon.
