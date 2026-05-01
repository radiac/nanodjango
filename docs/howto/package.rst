===============================
How to package a nanodjango app
===============================

You may want to add a nanodjango site to a bigger project, or you may want to turn a
nanodjango app into a standalone project on PyPI (such as
`privipod <https://github.com/radiac/privipod>`_, a nanodjango-based secret sharing
tool).

To do this, you may want to put your nanodjango script inside a package - for example:

```
    myproject/
      __init__.py
      __main__.py
      app.py
```

where ``app.py`` is your nanodjango script, and you want to launch it from
``__main__.py`` - but using the name of your package, ``myproject``.

Nanodjango was always designed and intended to be run as a single file, where it picks
up the app name from the file name. However, needs must, so there is limited support
for what you're trying to do.

However, be warned: **here be dragons**.


Running with a different name
=============================

When you instantiate ``Django``, pass it the ``APP_NAME`` of your containing package:

.. code-block:: python

    app = Django(APP_NAME="myproject")


This is going to fix your paths and module lookups so that your nanodjango script will
think it's actually called "myproject", and it'll look for its static files, templates,
migrations etc in your ``myproject/`` dir - ie ``myproject/static/`` etc.


Potential issues
----------------

However, I warned you there are dragons:

* This approach has not been widely used, and is likely break in exciting ways if you
  push it too far.
* This also means it'll expect your ``myproject/templates/`` etc are intended for your
  nanodjango app;
* ... which means anything under ``myproject/static/`` and ``myproject/public/`` will be
  public to anyone who can access the webserver;
* ... and it'll overwrite anything in ``myproject/static-collected/`` if you're running
  in production mode;
* ... and it'll create any migrations it needs to in ``myproject/migrations/``.
* It will be treating your ``myproject/`` dir as your project root - so your default
  sqlite database will also end up in your Python installation's ``site-packages``,
  which means it's not exactly safe.

So, non-exhaustive list of things you will want to do:

* **Specify a different database path**
* **Always ship with complete migrations** (or never ship migrations) - you could end up
  with clashes if your users' migration history doesn't match yours
* **Be careful to avoid directory name clashes** - perhaps specify custom paths for
  static, public, templates, static-collected, migrations etc.


How to actually get it to run
=============================

Your ``__main__.py`` *could* look something like this:

.. code-block:: python

    from .app import app

    if __name__ == "__main__":
        app.run()

But chance are you're going to want to control the ``Django`` settings before you
instantiate it. The easiest pattern for this is probably to set some global variables
somewhere before you import your app; for example, you could have this setup:

.. code-block:: python
    # myproject/config.py
    DEBUG = False


    # myproject/__main__.py
    import sys
    from .import config

    if __name__ == "__main__":
        if sys.ARGV[0] == "--debug":
            config.DEBUG = True

        # Only import app.py after config.py is configured
        from .app import app
        app.run()


    # myproject/app.py
    from . import config
    from nanodjango import Django

    app = Django(DEBUG=config.DEBUG)


You can see this is a convoluted and messy pattern, but it works. There are other
approaches, but this is probably the simplest way to crowbar an existing script into a
package.
