=====
Views
=====

Registering routes
==================

Routes with ``path()``
----------------------

Once you create your ``app = Django()``, you can use the ``@app.path`` decorator to
define routes and views:

.. code-block:: python

    @app.path("")
    def index(request):
        ...

This can start with a leading ``/`` like Flask, or without as with Django.

This uses Django's standard `path`__ function, so the standard path converters work as expected:

__ https://docs.djangoproject.com/en/5.2/ref/urls/#django.urls.path

.. code-block:: python

    @app.path("articles/<int:year>/<int:month>/<slug:slug>/")
    def article_detail(request, year, month, slug):
        ...


Routes with ``re_path()``
-------------------------

You can use the ``@app.re_path`` decorator to define routes with a regular expression:

.. code-block:: python

    @app.re_path(r"authors/(?P<slug>[a-z]{3,})/")
    def author_detail(request, slug):
        ...

This uses Django's standard `re_path`__ function, so the standard path converters work as expected:

__ https://docs.djangoproject.com/en/5.2/ref/urls/#django.urls.re_path


Routes with ``re_route()``
--------------------------

This is the legacy underlying function for decorating routes:

* ``app.path('/')`` is equivalent to ``app.route('/')``
* ``app.path_re(r".*")`` is equivalent to ``app.route(r".*", re=True)``

You are encouraged to use the Django-compatible ``.path()`` and ``.re_path()`` for
consistency with full Django projects. but ``.route()`` will continue to exist for
backwards compatibility and familiarity for those coming from other frameworks.


Including other urlconfs
------------------------

Call ``app.path(..)`` or ``app.re_path(..)`` directly with ``include=urlconf`` to
include another urlconf in your urls:

.. code-block:: python

    # Add a django-ninja API
    from ninja import NinjaAPI
    api = NinjaAPI()
    app.path("api/", api.urls)

    # Add a django-fastview viewgroup
    from fastview.viewgroups.auth import AuthViewGroup
    app.re_path("accounts/", AuthViewGroup().include())


Return values
=============

With nanodjango you can return a plain string value for convenience:

.. code-block:: python

    @app.path("/")
    def hello_world(request):
        return "<p>Hello, World!</p>"


or you can return an ``HttpResponse`` as you would with a normal Django view:

.. code-block:: python

    @app.path("/")
    def hello_world(request) -> HttpResponse:
        return HttpResponse("<p>Hello, World!</p>")

Note that we've added a type hint for the return value here - without that, ``nanodjango
convert`` won't know the return type, and will add a decorator to force it to an
``HttpResponse`` to be safe.


Additional decorators
=====================

The view function can be decorated with other decorators - just make sure the path
decorators are always the first decorator:

.. code-block:: python

    @app.route("/")
    @login_required
    def count(request):
        return "Hello world"


Class-based views
=================

Although most of the examples use function-based views, the path decorators also work on
standard class-based views:

.. code-block:: python

    @app.path("/counts/")
    class Counts(ListView):
        model = CountLog


Async views
===========

The path decorators can also decorate async views:

.. code-block:: python

    @app.route("/slow/")
    async def slow(request):
        import asyncio
        await asyncio.sleep(10)
        return "Async views supported"
