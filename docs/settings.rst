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

``MIGRATIONS_DIR``
  The directory name for migrations. Useful if you have more than one app script in the
  same dir - such as the examples dir for this project.

``PUBLIC_DIR``
  If set, nanodjango will use it to set ``WHITENOISE_ROOT``, so any files inside are
  served from the site root. Useful for ``favicon.ico``, ``robots.txt`` etc.
