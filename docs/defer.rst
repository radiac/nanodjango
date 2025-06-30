================
Deferred Imports
================

Nanodjango configures Django to run from a single file when ``app = Django()`` is
called.

This can be a problem for packages which expect that Django will be configured and ready
to access settings as soon as they are imported, or if they define models. Placing these
imports before ``Django()`` is called can result in unexpected behaviour or errors.

For example, if we want to import Django's standard ``auth.User`` model, it will fail
because Django hasn't been configured yet:

.. code-block:: python

    from nanodjango import Django
    from django.contrib.auth.models import User  # this line will fail to import

    app = Django()

    @app.route("/")
    def home(request):
        print(f"There are {User.objects.count()} users")


To solve this, we need to make the ``Django()`` call *before* the module is imported,
but this is often inconvenient and can violate PEP8.

Nanodjango solves this by providing support for **deferred imports**.


``nanodjango.defer``
====================

Deferred imports are controlled with ``nanodjango.defer`` - a context manager which
captures any imports, replaces the imported symbols with placeholders, and delays the
actual import until after Django has been set up.

To fix the script above we move the import into a ``defer`` context:

.. code-block:: python

    from nanodjango import Django, defer

    with defer:
        from django.contrib.auth.models import User

    app = Django()

    @app.route("/")
    def home(request):
        print(f"There are {User.objects.count()} users")

You can have multiple imports in a single ``defer``, and multiple ``defer`` sections
before ``Django()`` is instantiated - but none after.

You cannot access a deferred import until after ``Django()`` has been called.


``nanodjango.defer.optional``
=============================

Sometimes you'll want to try importing something if it is available:

.. code-block:: python

    from nanodjango import Django

    try:
        import some_package
    except ImportError:
        some_package = None

    app = Django()

    @app.route("/")
    def home(request):
        print(f"some_package {'is' if some_package else 'is not'} installed")

Because the import is not performed until later, the ``ImportError`` will not be raised
until ``Django()`` is called and the deferred imports are imported.

To get around this, you can use ``defer.optional``:

.. code-block:: python

    from nanodjango import Django, defer

    with defer.optional:
        import some_package

    app = Django()

    @app.route("/")
    def home(request):
        print(f"some_package {'is' if some_package else 'is not'} installed")

If the package is not found during ``Django()``, it will be set to ``None``.

You can have a mix of ``defer`` and ``defer.optional`` contexts before ``Django()`` is
called.


``nanodjango.defer.is_installed(name)``
=======================================

The optional deferral may not go far enough if you need to check for the package before
``Django()`` - perhaps you need additional Django settings if it is present, or you are
using the ``django_pre_setup`` hook.

To help with this, the ``defer.is_installed(name)`` function will return ``True`` if the
named package is installed, or ``False`` if it is not, without actually trying to import
it.

For example::

.. code-block:: python

    from nanodjango import Django, defer

    with defer.optional:
        import some_package

    settings = {}
    if defer.is_installed("some_package"):
        settings['MY_PACKAGE_VAR'] = True

    app = Django(**settings)
