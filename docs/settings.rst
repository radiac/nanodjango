========
Settings
========

Module-level settings
=====================

The simplest way to configure Django is to define settings as module-level uppercase
variables in your script::

    from nanodjango import Django  # isort: skip

    DEBUG = False
    SECRET_KEY = os.environ["SECRET_KEY"]
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "my.example.com"]

    app = Django()

These settings are extracted from your source file during ``from nanodjango import Django``
via AST parsing, so they're available before any Django imports. This enables PEP8-compliant
import ordering - you can place Django imports at the top of your file.

You can also reference other settings in your definitions::

    from nanodjango import Django  # isort: skip

    DEBUG = False
    STATIC_ROOT = BASE_DIR / "collected-static"

    app = Django()

``BASE_DIR`` and ``Path`` are automatically available for use in your settings.


How it works
------------

Module-level settings work in two phases:

1. **Early extraction (AST parsing)**: When you ``from nanodjango import Django``,
   simple settings are extracted via AST parsing to bootstrap Django. This allows
   Django imports to work immediately.

2. **Late update (at Django() instantiation)**: When you call ``app = Django()``,
   your module has fully executed. Any settings that couldn't be extracted earlier
   (conditionals, function calls, etc.) are now picked up from the module namespace.

This means complex settings patterns work::

    from nanodjango import Django  # isort: skip
    import os

    # Conditional settings - applied when Django() is called
    if os.environ.get("PRODUCTION"):
        DEBUG = False
        ALLOWED_HOSTS = ["example.com"]
    else:
        DEBUG = True
        ALLOWED_HOSTS = ["*"]

    # Computed settings
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-fallback")

    app = Django()  # Complex settings are applied here


Limitations
-----------

**Import order matters**
  ``from nanodjango import Django`` must appear before any Django imports that require
  configuration (like ``from django.contrib.auth.models import User``). Use
  ``# isort: skip`` to prevent formatters from reordering.

**Critical settings must be simple for early extraction**
  Settings needed to bootstrap Django (like ``INSTALLED_APPS`` and ``DATABASES``)
  should be simple assignments so they can be extracted via AST. Complex settings
  that aren't needed until later will be picked up when ``Django()`` is called.

**Available context for early extraction**
  When simple settings are evaluated during early extraction, the following are available:

  - ``BASE_DIR`` - Path to the directory containing your script
  - ``Path`` - ``pathlib.Path`` class
  - ``os`` - The ``os`` module
  - Any settings defined earlier in the file


Constructor settings
====================

You can also pass settings into your ``Django(..)`` object constructor::

    app = Django(
      ALLOWED_HOSTS=["localhost", "127.0.0.1", "my.example.com"],
      SECRET_KEY=os.environ["SECRET_KEY"],
      DEBUG=False,
    )

Constructor settings override module-level settings if both are specified.


Extra settings
==============

In addition to the standard Django settings, nanodjango provides some special settings
to configure itself and to simplify configuring Django:

``ADMIN_URL``
  The URL to serve the admin site from. If not set, the admin site will only be served
  if there are models registered with ``@app.admin``.

``API_URL``
  The URL to serve the Ninja API from - defaults to ``/api/``. This is only set up if
  there are API endpoints defined.

``EXTRA_APPS``
  List of apps to be appended to the standard ``INSTALLED_APPS`` setting.

``SQLITE_DATABASE``
  The path to the SQLite database file. This is a shortcut to configure the default
  ``DATABASES`` setting. If ``DATABASES`` is set, it will override this value.

``MIGRATIONS_DIR``
  The directory name for migrations. Useful if you have more than one app script in the
  same dir - such as the examples dir for this project.

``PUBLIC_DIR``
  If set, nanodjango will use it to set ``WHITENOISE_ROOT``, so any files inside are
  served from the site root. Useful for ``favicon.ico``, ``robots.txt`` etc.
