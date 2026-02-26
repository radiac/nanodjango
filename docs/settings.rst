========
Settings
========

Override Django's default settings by passing them into your ``Django(..)`` object
constructor, eg::

    app = Django(
      ALLOWED_HOSTS=["localhost", "127.0.0.1", "my.example.com"],
      SECRET_KEY=os.environ["SECRET_KEY"],
      DEBUG=False,
    )


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

  **In-memory database** - Use ``Django.SQLITE_MEMORY``::

    app = Django(SQLITE_DATABASE=Django.SQLITE_MEMORY)

  However, note that because both gunicorn (production sync) and uvicorn's auto-reload
  (async) spawn new processes which cannot access the database.

  This is therefore only recommended for sync apps used with ``nanodjango run``, or
  where databases are not needed. In other cases, consider a temporary file database.

  **Temporary file database** - Use ``Django.SQLITE_TMP``::

    app = Django(SQLITE_DATABASE=Django.SQLITE_TMP)

  This creates a temporary SQLite file in your system's temp directory that works with
  all run modes, so is the recommended option for ephemeral databases.

``MIGRATIONS_DIR``
  The directory name for migrations. Useful if you have more than one app script in the
  same dir - such as the examples dir for this project.

``PUBLIC_DIR``
  If set, nanodjango will use it to set ``WHITENOISE_ROOT``, so any files inside are
  served from the site root. Useful for ``favicon.ico``, ``robots.txt`` etc.


Settings callbacks
==================

You can use callbacks to modify nanodjango's default settings rather than replacing
them entirely. If you pass a callable for a setting that already exists in
nanodjango's defaults, it will be called with the current value and the return
value will be used::

    app = Django(
        MIDDLEWARE=lambda m: [MyPreMiddleware] + m + [MyPostMiddleware],
        INSTALLED_APPS=lambda apps: [a for a in apps if "admin" not in a],
    )

This is useful for prepending or appending to list settings like ``MIDDLEWARE`` or
``INSTALLED_APPS``, or for filtering out unwanted defaults.

Note that this only applies to settings that already exist in nanodjango's defaults.
For new settings that don't exist yet, callable values are stored as-is (this allows
you to pass callable settings like ``WHITENOISE_ADD_HEADERS_FUNCTION``).
