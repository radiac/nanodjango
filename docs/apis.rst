====
APIs
====

You can build an API using any method you would in a full Django project, but nanodjango
has built-in support for `Django Ninja <https://django-ninja.dev/>`_.


API decorator
=============

The ``@app.api`` decorator is an instance of ``NinjaAPI`` which is automatically
registered at the URL ``/api/``. This gives you an easy way to define your API
endpoints:

.. code-block:: python

    class Item(app.ninja.Schema):
        foo: str
        bar: float

    @app.api.get("/add")
    def add(request, a: int, b: int):
        return {"result": a + b}


See the `Django Ninja documentation <https://django-ninja.dev/>`_ for more details of
how to use the ``NinjaAPI`` instance at ``@app.api``.


Other Ninja features
====================

The ``app.ninja`` attribute provides a convenient way to access additional Ninja
features without importing, eg:

.. code-block:: python

    class Item(app.ninja.Schema):
        foo: str
        bar: float

    @app.api.post('/do_something')
    def do_something(
        request,
        item: Item,
        file: app.ninja.UploadedFile = app.ninja.File(..)
    ):
        ...


Why not import Ninja directly?
------------------------------

Although you can import Django Ninja directly, we currently recommend that you use the
``app.ninja`` attribute to avoid an issue with import order.

If you do want to ``import ninja``, you need  **initialise nanodjango.Django first**:

.. code-block:: python

    from nanodjango import Django
    app = Django()

    from ninja import NinjaAPI
    api = NinjaAPI()

    @api.get("/add")
    def add(request):
        CountLog.objects.create()

    app.route("api/", include=api.urls)


This is because the ``ninja`` module currently accesses Django settings when it is
imported. This is normally not an issue in a full Django project, because the apps are
loaded after settings, but in nanodjango everything is all in one file, where we
configure Django with our call to ``app = Django(..)``. See :doc:`troubleshooting` for
more details.

Unfortunately this goes against PEP 8, and will lead to messy code if you use a code
formatter like black or ruff - hence the ``app.ninja`` helper.

We hope this is only a temporary issue, but it will require a change in Django Ninja -
see `Ninja issue 1169 <https://github.com/vitalik/django-ninja/issues/1169>`_ for
details and progress.
