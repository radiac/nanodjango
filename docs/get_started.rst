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
        # Standard Django model, registered with the admin site
        timestamp = models.DateTimeField(auto_now_add=True)

    @app.route("/")
    def count(request):
        # Standard Django function view, or class-based view
        CountLog.objects.create()
        return f"<p>Number of page loads: {CountLog.objects.count()}</p>"

    @app.api.get("/add")
    def add(request):
        # Django Ninja API support built in
        CountLog.objects.create()
        return {"count": CountLog.objects.count()}

    @app.route("/slow/")
    async def slow(request):
        import asyncio
        await asyncio.sleep(10)
        return "Async views supported"


Now use the ``run`` command to create the migrations, apply them, and run your
project:

.. code-block:: bash

    nanodjango run counter.py

or you could run each step manually using Django management commands:

.. code-block:: bash

    nanodjango manage counter.py makemigrations counter
    nanodjango manage counter.py migrate
    nanodjango manage counter.py createsuperuser
    nanodjango manage counter.py

Serve it in production using gunicorn:

.. code-block:: bash

    nanodjango serve counter.py


or automatically convert it to a full Django app:

.. code-block:: bash

    nanodjango counter.py convert /path/to/site --name=myproject


To learn more about how this works, take a look at the :doc:`tutorial`.
