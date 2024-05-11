========
Tutorial
========

Lets look at how to write the :doc:`get_started` sample and use the key features.


Initialise nanodjango
=====================

First we import ``nanodjango`` and create a ``Django`` instance:

.. code-block:: python

    from nanodjango import Django

    app = Django(ADMIN_URL="admin/")

The ``Django`` instance, along with the ``nanodjango`` command, performs the magic
needed to make everything work in one file.

We can pass any Django settings into the constructor as named keywords. Above we pass a
special nanodjango setting ``ADMIN_URL``, which tells nanodjango where to serve the
admin site.

We could also configure other aspects of Django, for example:

.. code-block:: python

    app = Django(
        ADMIN_URL="admin/",
        SECRET_KEY=os.environ["DJANGO_SECRET_KEY"],
        ALLOWED_HOSTS=["localhost", "my.example.com"],
        DEBUG=False,
    )

For a full list of special nanodjango settings, see :doc:`settings`.


Create a view
=============

In nanodjango a view is a function which is decorated with ``app.route``:

.. code-block:: python

    @app.route("/")
    def count(request):
        ...

The ``@app.route("/")`` decorator serves this view at the url ``/``, and the view
function is passed the request as it would in a normal Django project.

From there we can do anything we would in a normal Django view - eg add more decorators,
process the request, use Django forms. We then either return a standard Django
``HttpResponse``, or nanodjango also lets you return a plain string for convenience.

For full details on ``app.route``, including how to specify regular expression paths and
include other urlconfs, see :doc:`views`.


Create a model
==============

Django models work exactly the same way as in Django, except you define them in the same
file, and they must be defined after ``app = Django()``:

.. code-block:: python

    from django.db import models

    app = Django(ADMIN_URL="admin/")

    class CountLog(models.Model):
        timestamp = models.DateTimeField(auto_now_add=True)


We can now create migrations for the app and apply them:

.. code-block:: bash

    nanodjango counter.py run makemigrations counter
    nanodjango counter.py run migrate

For full details on how to use Django management commands with nanodjango, see
:doc:`management`.


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

First enable the admin site by providing an ``ADMIN_URL`` setting, then decorate your
models with the ``app.admin`` decorator:

.. code-block:: python

    app = Django(ADMIN_URL="admin/")

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


Deploy to production
====================

The ``Django`` app instance supports WSGI, so for gunicorn it would be:

.. code-block:: bash

    gunicorn -w 4 counter:app

or for uwsgi:

.. code-block:: bash

    uwsgi --wsgi-file counter.py --callable app --processes 4


Convert to a full Django project
================================

When you reach the point where you have several views or models, you may want to think
about converting your app into a full Django project.

You can do this with:

.. code-block:: bash

    nanodjango counter.py convert /path/to/site --name=myproject

This will create a Django project at ``/path/to/site/myproject``, and unpack your single
file into a full app at ``/path/to/site/myproject/counter``. Your sqlite database,
migrations, templates and static files will be copied across, if you have them, and in
many cases it should run straight away:

.. code-block:: bash

    cd /path/to/site
    ./manage.py runserver 0:8000

For full details on how to use nanodjango's ``convert`` command, see :doc:`convert`.
