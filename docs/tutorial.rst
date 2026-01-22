========
Tutorial
========

Lets look at how to write the :doc:`get_started` sample and use the key features.


Initialise nanodjango
=====================

First we import ``nanodjango`` and create a ``Django`` instance:

.. code-block:: python

    from nanodjango import Django

    app = Django()

The ``Django`` instance, along with the ``nanodjango`` command, performs the magic
needed to make everything work in one file.

We can pass Django settings into the constructor as named keywords. We don't do it above
as nanodjango has sensible defaults, but you can pass in any standard Django setting,
plus some extra ones that nanodjango uses, like ``ADMIN_URL``:

.. code-block:: python

    app = Django(
        ADMIN_URL="secret_admin/",
        SECRET_KEY=os.environ["DJANGO_SECRET_KEY"],
        ALLOWED_HOSTS=["localhost", "my.example.com"],
        DEBUG=False,
    )

For a full list of special nanodjango settings, see :doc:`settings`.


Create a view
=============

In nanodjango a view is a function which is decorated with ``@app.route``:

.. code-block:: python

    @app.route("/")
    def count(request):
        ...

The ``@app.route("/")`` decorator serves this view at the url ``/``, and the view
function is passed the request as it would in a normal Django project. You can decorate
both normal and async views in the same way.

From there we can do anything we would in a normal Django view - eg add more decorators,
process the request, use Django forms. We then either return a standard Django
``HttpResponse``, or nanodjango also lets you return a plain string for convenience.

For full details on ``app.route``, including how to specify regular expression paths and
include other urlconfs, see :doc:`views`.


Create an API endpoint
======================

We use `Django Ninja <https://django-ninja.dev/>`_ to provide a simple syntax for
defining APIs - nanodjango provides a convenient ``@app.api`` decorator which
initialises and registers a ``NinjaAPI`` instance:

.. code-block:: python

    @app.api.get("/hello")
    def hello(request):
        return {"message": "Hello!"}

For more details on working with Django Ninja in nanodjango, see :doc:`apis`.


Create a model
==============

Django models work exactly the same way as in Django, except you define them in the same
file. When running your script directly (``python counter.py``), Django is configured
as soon as you ``from nanodjango import Django``, so you can define models anywhere after
that import:

.. code-block:: python

    from nanodjango import Django  # isort: skip
    from django.db import models

    app = Django()

    class CountLog(models.Model):
        timestamp = models.DateTimeField(auto_now_add=True)


We can now run the script, which will create migrations for the app and apply them:

.. code-block:: bash

    nanodjango run counter.py

You could also create migrations manually without running:

.. code-block:: bash

    nanodjango manage counter.py makemigrations counter

For full details on how to use Django management commands with nanodjango, see
:doc:`usage`.


Use the model
=============

Once the model is defined, you can use it in a view as you would any normal Django model
and view:

.. code-block:: python

    @app.route("/")
    def count(request):
        CountLog.objects.create()
        return f"<p>Number of page loads: {CountLog.objects.count()}</p>"


This just creates an object at every request and reports on how many objects there are,
but you could use it with a ``ModelForm`` just like a normal Django model and view.

A more complicated example could look like this:

.. code-block:: python

    @app.admin
    class Author(models.Model):
        name = models.CharField(max_length=100)
        birth_date = models.DateField(blank=True, null=True)

    class AuthorForm(ModelForm):
        class Meta:
            model = Author
            fields = ["name", "birth_date"]

    @app.route("add/")
    def add_author(request):
        form = AuthorForm(request.POST or None)
        if form.is_valid():
            form.save()
            return "Author added"
        return render(request, "form.html", {'form': form})


Use the admin site
==================

To add a model to the admin site, decorate your models with the ``app.admin`` decorator:

.. code-block:: python

    @app.admin
    class CountLog(models.Model):
        ...


This decorator also lets you configure your ``ModelAdmin`` by passing class attributes:

.. code-block:: python

    @app.admin(
        list_display=["id", "timestamp"],
        readonly_fields=["timestamp"],
    )
    class CountLog(models.Model):
        ...


Using the decorator anywhere in your script will automatically enable the admin site.
You can customise the url with ``ADMIN_SITE``, or use the setting to force the admin
site to be active even if you're not using the decorator anywhere.:

.. code-block:: python

    app = Django(ADMIN_URL="admin/")


Deploy to production
====================

Nanodjango has a built-in command to run your script in production mode, with debug
turned off, using whitenoise, gunicorn or uvicorn, and sensible defaults::

    nanodjango serve counter.py

If you want more control, you can also pass the ``Django`` instance to a WSGI or ASGI
server directly:

.. code-block:: bash

    gunicorn -w 4 counter:app
    uwsgi --module counter:app --processes 4 --http=0.0.0.0:8000
    uvicorn counter:app


Convert to a full Django project
================================

When you reach the point where you have several views or models, you may want to think
about converting your app into a full Django project.

You can do this with:

.. code-block:: bash

    nanodjango convert counter.py /path/to/site --name=myproject

This will create a Django project at ``/path/to/site/myproject``, and unpack your single
file into a full app at ``/path/to/site/myproject/counter``. Your sqlite database,
migrations, templates and static files will be copied across, if you have them, and in
many cases it should run straight away:

.. code-block:: bash

    cd /path/to/site
    ./manage.py runserver 0:8000

For full details on how to use nanodjango's ``convert`` command, see :doc:`convert`.
