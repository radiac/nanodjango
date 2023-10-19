=============
django-flasky
=============

Write a Django site which looks like Flask, then turn it into a proper Django site when
it starts to get complicated.

.. image:: https://img.shields.io/pypi/v/django-flasky.svg
    :target: https://pypi.org/project/django-flasky/
    :alt: PyPI

.. image:: https://github.com/radiac/django-flasky/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/radiac/django-flasky/actions/workflows/ci.yml
    :alt: Tests

.. image:: https://codecov.io/gh/radiac/django-flasky/branch/main/graph/badge.svg?token=BCNM45T6GI
    :target: https://codecov.io/gh/radiac/django-flasky
    :alt: Test coverage


Quickstart
==========

Install django-flasky::

    pip install django-flasky


Write a Django app in the same style as you would a Flask app, but using models and other Django goodness:

.. code-block:: python

    from django.db import models
    from django_flasky import Django

    app = Django()

    class CountLog(models.Model):
        timestamp = models.DateTimeField(auto_now_add=True)

    @app.route("/")
    def count(request):
        CountLog.objects.create()
        return f"<p>Number of page loads: {CountLog.objects.count()}</p>"

Save that as ``counter.py`` and run it with:

.. code-block:: sh

    django-flasky counter.py run migrate
    django-flasky counter.py run

It will create your database in a ``db.sqlite3`` file next to your ``counter.py``.


Why would you do this? Why?
===========================

Developers often begin projects with Flask because it looks easier to get started with
than Django, but as the project grows it's easy for it to become an unmaintainable
mashup of third party libraries and hand-rolled bodges just to begin to get close to
what Django offers out of the box.

As someone who has often been brought in to try to rescue these projects, I decided that
enough is enough - it is time to eliminate that excuse for picking Flask over Django.

Django-Flasky makes it as easy to start a Django project as it is to start a Flask
project, but because it's using Django from the start you'll be able to take advantage
of everything that Django has to offer - models, admin, forms, and the rest - and then
switch to a normal Django site structure when you're ready to do things properly.


Using django-flasky
===================

Settings
--------

Override settings by passing them into your ``Django(..)`` object constructor, eg:

.. code-block:: python

    app = Django(SECRET_KEY="some-secret", ALLOWED_HOSTS=["lol.example.com"])


Templates and static files
--------------------------

Place your templates and static assets next to ``hello_world.py``, under a ``templates``
and ``static`` directory respectively.


Limitations
===========

Django really doesn't like running from a single file, so measures were taken during the
development of Django-Flasky which may lead to problems as your project grows.

It is strongly recommended that this project is not used for anything serious.


Converting to a sensible Django project
=======================================

Once you've got a couple of models and views, you'll start thinking "Hey, maybe I should
start splitting this project into apps". You are correct, and now is the time to turn
your project into an actual Django project.

One day you will be able to run:

.. code-block:: sh

    django-flasky hello.py upgrade

This will do its best to break up your ``hello_world.py`` into a proper Django project
under ``hello_world``.

Right now though, this is not implemented, so you'll just need to do it yourself - put
your models in your ``models.py``, your views in ``views.py`` and routes in ``urls.py``.
