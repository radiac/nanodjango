============
Internal API
============

This document describes the internal Python API for nanodjango, primarily for advanced
users, plugin developers, and contributors.


.. _internal_api.django:

``nanodjango.Django``
=====================

The main application class for nanodjango. This class orchestrates the entire single-file
Django application lifecycle, from initial configuration through to serving requests.

.. important::
   Only one ``Django()`` instance is allowed per script. Creating a second instance will
   raise a ``ConfigurationError``.


API reference
-------------

.. autoclass:: nanodjango.Django
    :members:
    :show-inheritance:


.. _internal_api.defer:

``nanodjango.defer``
====================

The deferred import system allows nanodjango to register Django components (models,
views, admin, etc.) before Django itself is fully configured. This solves the circular
dependency problem inherent in Django's initialization.


Overview
--------

Django requires configuration to be complete before you can import most of its
components. However, in a single-file application, you want to define models and views
at the module level, which happens during import. The defer system resolves this by:

1. Intercepting import statements within a context manager
2. Recording what should be imported without actually importing it
3. Executing the real imports after Django is configured

Usage::

    from nanodjango import Django
    from nanodjango.defer import defer

    app = Django()

    # These imports are deferred until Django is configured
    with defer:
        from django.db import models
        from django.contrib.auth.models import User

    # Later, after Django setup, imports are applied
    defer.apply()  # This happens automatically in Django.__init__


API reference
-------------

.. autoclass:: nanodjango.defer.ImportDeferrer
    :members:
    :show-inheritance:

.. autoclass:: nanodjango.defer.DeferredImport
    :members:
    :show-inheritance:

.. autoexception:: nanodjango.defer.DeferredUsageError
    :show-inheritance:

.. autoexception:: nanodjango.defer.DeferredImportError
    :show-inheritance:

.. autoexception:: nanodjango.defer.DeferredModuleNotFoundError
    :show-inheritance:

.. autoexception:: nanodjango.defer.DeferredAttributeError
    :show-inheritance:
