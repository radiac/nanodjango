================
Deferred Imports
================

.. note::

   As of version 0.14, nanodjango configures Django during
   ``from nanodjango import Django``, which means Django imports usually work without
   any special handling. This works in both direct mode (``python script.py``) and
   CLI mode (``nanodjango run script.py``).

   Deferred imports are now only needed for unusual third-party packages that perform
   initialization at import time in ways that conflict with early configuration.

Django is configured as soon as you import the ``Django`` class from nanodjango.
This means Django imports work naturally:

.. code-block:: python

    from nanodjango import Django  # isort: skip
    from django.db import models
    from django.contrib.auth.models import User

    app = Django()

    @app.route("/")
    def home(request):
        print(f"There are {User.objects.count()} users")

Nanodjango provides support for **deferred imports** to handle edge cases with
third-party packages.


``nanodjango.defer``
====================

Deferred imports are controlled with ``nanodjango.defer`` - a context manager which
captures any imports, replaces the imported symbols with placeholders, and delays the
actual import until after Django has been set up.

For example, if a third-party package requires Django to be fully configured at import
time, you can use ``defer``:

.. code-block:: python

    from nanodjango import Django, defer

    with defer:
        from some_django_package import SomeClass  # imported after Django setup

    app = Django()

    @app.route("/")
    def home(request):
        return SomeClass.do_something()

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

For example:

.. code-block:: python

    from nanodjango import Django, defer

    with defer.optional:
        import some_package

    settings = {}
    if defer.is_installed("some_package"):
        settings['MY_PACKAGE_VAR'] = True

    app = Django(**settings)
