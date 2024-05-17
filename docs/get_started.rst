===============
Getting started
===============

Installation
============

Install nanodjango:

.. code-block:: bash

    pip install nanodjango



Your first app
==============

Create a new file, ``counter.py`` with the following:

.. code-block:: python

    from django.db import models
    from nanodjango import Django

    app = Django()

    @app.admin
    class CountLog(models.Model):
        timestamp = models.DateTimeField(auto_now_add=True)

    @app.route("/")
    def count(request):
        CountLog.objects.create()
        return f"<p>Number of page loads: {CountLog.objects.count()}</p>"

Now use the ``start`` command to create the migrations, apply them, and run your
project:

.. code-block:: bash

    nanodjango start counter.py

or you could run each step manually:

.. code-block:: bash
    nanodjango run counter.py makemigrations counter
    nanodjango run counter.py migrate
    nanodjango run counter.py createsuperuser
    nanodjango run counter.py

Run it in production using WSGI:

.. code-block:: bash

    gunicorn -w 4 counter:app


or automatically convert it to a full Django app:

.. code-block:: bash

    nanodjango counter.py convert /path/to/site --name=myproject


To learn more about how this works, take a look at the :doc:`tutorial`.
