=============
django-flasky
=============

Write a Django site in a single file, using views, models and admin, then automatically
convert it to a full Django project when you're ready for it to grow.

Perfect for experiments, prototypes, tutorials, and small applications.

.. image:: https://img.shields.io/pypi/v/django-flasky.svg
    :target: https://pypi.org/project/django-flasky/
    :alt: PyPI

.. image:: https://github.com/radiac/django-flasky/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/radiac/django-flasky/actions/workflows/ci.yml
    :alt: Tests

.. image:: https://codecov.io/gh/radiac/django-flasky/branch/main/graph/badge.svg?token=BCNM45T6GI
    :target: https://codecov.io/gh/radiac/django-flasky
    :alt: Test coverage

Features:

* Views and routes
* Models and admin
* Automatic conversion to a full Django project


Quickstart
==========

Install django-flasky::

    pip install django-flasky


Write a Django app in the same style as you would a Flask app, but using models, admin,
and other Django goodness:

.. code-block:: python

    from django.db import models
    from django_flasky import Django

    app = Django(ADMIN_URL="admin/")

    @app.admin
    class CountLog(models.Model):
        timestamp = models.DateTimeField(auto_now_add=True)

    @app.route("/")
    def count(request):
        CountLog.objects.create()
        return f"<p>Number of page loads: {CountLog.objects.count()}</p>"

Save that as ``counter.py``, then set up your database and run it with:

.. code-block:: sh

    django-flasky counter.py run migrate
    django_flasky counter.py run createsuperuser
    django-flasky counter.py run

It will create your database in a ``db.sqlite3`` file next to your ``counter.py``, with
the appropriate migrations in ``migrations/``.


Writing django-flasky apps
==========================

Django-flasky expects your application to be called ``app``, and it must be defined
before any models.


Settings
--------

Override settings by passing them into your ``Django(..)`` object constructor, eg:

.. code-block:: python

    app = Django(SECRET_KEY="some-secret", ALLOWED_HOSTS=["lol.example.com"])

To enable the admin site, add ``ADMIN_URL``:

.. code-block:: python

    app = Django(SECRET_KEY="some-secret", ADMIN_URL="/admin/")

You can use all the standard Django settings, plus some special settings to configure
django-flasky or simplify common setting changes:

``ADMIN_URL``:
  The URL to serve the admin site from. If not set, the admin site will _not_ be served.

``EXTRA_APPS``
  List of apps to be appended to the standard ``INSTALLED_APPS`` setting.

``SQLITE_DATABASE``
  The path to the SQLite database file. This is a shortcut to configure the default
  ``DATABASES`` setting. If ``DATABASES`` is set, it will override this value.

``MIGRATIONS_DIR``
  The directory name for migrations. Useful if you have more than one app script in the
  same dir - such as the examples dir for this project.


Templates and static files
--------------------------

Place your templates and static assets next to ``hello_world.py``, under a ``templates``
and ``static`` directory respectively.


Management commands
===================

The ``django-flasky`` command provides a convenient way to run Django management
commands on your app::

    django-flasky <script> run [<command>]

If the command is left out, it will default to ``runserver 0:8000`` - these two commands
are equivalent:

    django-flasky counter.py run
    django-flasky counter.py run runserver 0:8000

If your command would normally be ``manage.py migrate``, replace ``manage.py``::

    django-flasky counter.py run migrate

Note: for commands which need to know the name of the app, such as ``makemigrations``,
the app name is the filename - eg::

    django-flasky counter.py run makemigrations counter


Running in production
=====================

The ``app = Django()`` instance is also a WSGI application, so you can run your script
in production using a WSGI server such as gunicorn - specify the script name and app
instance variable::

    pip install gunicorn
    gunicorn -w 4 counter:app


Converting to a full Django project
===================================

Django really doesn't like running from a single file, so measures were taken during the
development of django-flasky which may lead to problems as your project grows. It is
therefore strongly recommended that this project is not used beyond its intended scope.

When you feel that your code has outgrown a single app in a single file, django-flasky
can help turn it into a full Django project.

Run:

.. code-block:: sh

    django-flasky hello.py convert path/to/new/project myproject

This will do its best to break up your ``hello_world.py`` into a proper Django project
called ``myproject``, with your code in an app called ``myproject.hello_world``.

If you've got an existing database, you can copy that over to your new project and
everything should run as it did before, just with more room to grow.

Please note that although django-flasky will try its hardest to get it right, there will
be a lot of edge cases that it doesn't understand, and you may still need to make some
changes after the conversion process.

With your help, this will get better over time - if you get an unhandled exception where
``convert`` failed to generate files at all, or you feel it has missed something
important that it should have handled better, please do raise an issue and take a look
at the documentation for contributing to the project.
