================================================
How to use nanodjango as a static site generator
================================================

Nanodjango's :doc:`integrations` make it perfect for use as a static site generator.


Using pip
=========

Add the relevant packages to your Python environment:

.. code-block:: bash

    pip install nanodjango django-nanopages django-browser-reload django-distill


Then put this minimal script in a Python file, eg ``website.py``:

.. code-block:: python

    from nanodjango import Django

    app = Django()
    app.pages("/", path="pages", context={"site_title": "nanopages example"})


You can now put markdown files in a ``pages/`` dir next to your script, and they'll get
picked up and rendered in views, with automatic reloads in your browser. You can then
use distill to build them into a static site:

.. code-block:: bash

    nanodjango manage website.py distill generate \
      --output-directory=output/ --collectstatic


Using uv
========

Alternatively you can wrap those lines up with an inline dependencies comment:

.. code-block:: python

    # /// script
    # dependencies = [
    #   "nanodjango",
    #   "django-style",
    #   "django-nanopages",
    #   "django-browser-reload",
    #   "django-distill",
    # ]
    # ///
    from nanodjango import Django

    app = Django(EXTRA_APPS=["django_style"])
    app.pages("/", path="pages", context={"site_title": "nanopages example"})


    if __name__ == "__main__":
        app.invoke(default="run")

and then use ``uv run`` to generate a virtual environment on the fly:

.. code-block:: bash

    uv run website.py manage distill generate \
      --output-directory=output/ --collectstatic


Add models and more
===================

Because this is all just sitting on top of Django, you can create models and manage them
through the admin site of a local runserver, then add views to render model data for
distill to pick up and turn into static content.


Further reading
===============

For full details on working with nanodjango, django-nanoppages and distill, see the
`django-nanopages documentation <https://django-nanopages.readthedocs.io/en/latest/>`_
or the accompanying
[nanodjango.dev blog post](https://nanodjango.dev/blog/2026-10-static-site-builder/).

