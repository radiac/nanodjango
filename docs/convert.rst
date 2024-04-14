===================================
Converting to a full Django project
===================================

Although nanodjango is great for simple applications and quick prototypes, it is
strongly recommended that it is not used beyond its intended scope. Anything more
complicated than a couple of models and views will benefit from Django's standard
project structure.

When you feel that your code has outgrown a single app in a single file, nanodjango
can help turn it into a full Django project::

    nanodjango counter.py convert path/to/new/project

It will do its best to break up your ``counter.py`` into a proper Django project,
with your code in an app inside the project called ``counter``.

It will also copy over any ``templates/`` and ``static/`` files, and if you've got an
sqlite database, it will copy that over to your new project along with ``migrations/``.
Everything should run as it did before - just with more room to grow.


The ``convert`` command
=======================

With all options, the ``convert`` command is::

    nanodjango <script.py> convert <target/path> --name=<project_name> --delete

The arguments are:

``<target/path>``:
    The root path to use as the target for ``django-admin startproject``

``--name=<project_name>``
    Specify the name of the project for ``django-admin startproject``.

    If not provided, defaults to ``project``

``--delete``
    If the target path exists, delete it before creating the new project.

    If it exists and this argument is not set, an error will be raised.

For example::

    nanodjango counter.py convert project --name=tracker --delete

* will create a new dir ``project`` next to ``counter.py``
* it will create a new Django project called ``tracker`` inside that dir, giving you
  ``project/manage.py`` and ``project/tracker/wsgi.py`` etc.
* it will create a new ``counter`` app within that project, with
  ``project/tracker/counter/views.py`` and all your urls, models etc


How it works
============

At a high level, nanodjango will:

#. Run ``django-admin startproject`` to create a base project template
#. Create an app within that project, using the name of your app script
#. Copy across any templates, static files and migrations, and your sqlite database if
   you have one
#. Extract your models and any objects they reference, and move them into ``models.py``
   in the app
#. Extract your ``@app.route`` decorated views and move them into ``views.py``
#. Use your routes to build ``urls.py``
#. Create an ``admin.py`` with your ``ModelAdmin`` definitions, if necessary
#. Any code which hasn't been referenced and used in the above files will be put in
   ``unused.py``. This code will not be used, it is for you to manually integrate into
   your new code structure.

Edge cases
==========

Although nanodjango will always try its hardest to get it right, there will be a lot of
edge cases that it doesn't understand, and you may still need to make some changes after
the conversion process.

Here are some things to look out for:


View return values
------------------

As explained in the :doc:`views` documentation, if you don't type-hint your view's
return value, nanodjango will add a ``@ensure_http_response`` decorator to the view.

At runtime this will detect when your view returns a ``str`` instead of an
``HttpResponse``, and convert it for you. In nanodjango this happens behind the scenes.

To avoid this, add a ``-> HttpResponse`` type hint (or subclass) for the return value,
nanodjango will recognise that the ``@ensure_http_response`` decorator is not needed,
eg::

    @app.route("/author/")
    def redirect(request) -> HttpResponseRedirect:
        return HttpResponseRedirect("https://radiac.net/")


Admin site
----------

Because ``convert`` builds on top of the standard ``django-admin startproject``
template, the admin site will always be enabled after conversion, regardless of your
``ADMIN_URL`` nanodjango setting.


Unused code
-----------

While splitting your file, nanodjango tracks references to code objects you have
imported and defined, and will copy them into the most relevant file - for example, if
your model and view both reference a constant, it will be put into ``models.py`` and
imported into ``views.py``.

If any objects are left at the end which you defined but haven't been used by your
settings, models, views or model admin definitions, they will be put into ``unused.py``
and not linked to from any active code.

If you see a warning that an ``unused.py`` was created during the conversion process,
you should move or delete the code inside, as appropriate.


Other issues
------------

With your help, this will get better over time - if you get an unhandled exception where
``convert`` failed to generate files at all, or you feel it has missed something
important that it should have handled better, please do raise an issue and take a look
at :doc:`contributing`.
