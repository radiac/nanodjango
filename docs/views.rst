=====
Views
=====

Once you create your ``app = Django()``, you can use the ``@app.route`` decorator to
define routes and views:

.. code-block:: python

    @app.route("/")
    def index(request):
        ...

Paths can start with a leading ``/`` as they do in Flask, but this is optional.

Behind the scenes, nanodjango uses `path`__ when it adds it to Django's URLs, so
the standard path converters work as expected:

__ https://docs.djangoproject.com/en/5.0/ref/urls/#django.urls.path

.. code-block:: python

    @app.route("articles/<int:year>/<int:month>/<slug:slug>/")
    def article_detail(request):
        ...


Return values
=============

With nanodjango you can return a plain string value for convenience:

.. code-block:: python

    @app.route("/")
    def hello_world(request):
        return "<p>Hello, World!</p>"


or you can return an ``HttpResponse`` as you would with a normal Django view:

.. code-block:: python

    @app.route("/")
    def hello_world(request) -> HttpResponse:
        return HttpResponse("<p>Hello, World!</p>")

Note that we've added a type hint for the return value here - without that, ``nanodjango
convert`` won't know the return type, and will add a decorator to force it to an
``HttpResponse`` to be safe.


Additional decorators
=====================

The view function can be decorated with other decorators - just make sure ``@app.route``
is always the first decorator:

.. code-block:: python

    @app.route("/")
    @login_required
    def count(request):
        return "Hello world"

