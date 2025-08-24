============
Integrations
============

Nanodjango provides built-in integration with several useful Django packages to
streamline development. Nanodjango's plugin system will automatically enable additional
functionality when these packages are installed.


Django Ninja API Framework
==========================

Nanodjango has a tight integration with `Django Ninja <https://django-ninja.dev/>`_ for
building APIs - see :doc:`apis` for more details.


Django Style
============

`Django Style <https://github.com/radiac/django-style>`_ adds basic tasteful designs to
your project by providing a default ``base.html`` template, which can be configured to
use plain CSS, Bootstrap or Tailwind, and to be in standard fluid mode, or app mode
with a fixed header and body height.

Install django-style::

    pip install django-style

Nanodjango will detect it and automatically add ``django_style`` to ``INSTALLED_APPS``.

You can then ``{% extends "base.html" %}`` in your templates, or customise the styles
and layouts - see the `django-style documentation
<https://django-style.readthedocs.io/en/latest/>`_ for more details.


Django Nanopages
================

`Django Nanopages <https://github.com/radiac/django-nanopages>`_ provides a simple way
to create site sections from directories containing markdown files. It's perfect for
using nanodjango as a static site builder when paired with Django Distill.

Install django-nanopages::

    pip install django-nanopages

Nanodjango will detect it and automatically:

* add ``django_nanopages`` to ``INSTALLED_APPS``;
* adds an ``app.pages(url_pattern, markdown_dir_path)`` method to register a nanopages
  site section.


Django Browser Reload
=====================

`Django Browser Reload <https://github.com/adamchainz/django-browser-reload>`_ provides
automatic browser reloading during development.

Install django-browser-reload::

    pip install django-browser-reload

Nanodjango will detect it and automatically:

* add ``django_browser_reload`` to ``INSTALLED_APPS``;
* add the browser reload middleware;
* mount reload URLs at ``/__reload__/``.

This integration works seamlessly with ``nanodjango run`` for automatic browser
refreshing during development.


Django Distill
==============

`Django Distill <https://github.com/meeb/django-distill>`_ generates static sites from
Django applications.

Install django-distill::

    pip install django-distill

Nanodjango will detect it and automatically:

* add ``django_distill`` to ``INSTALLED_APPS``;
* support Distill arguments to ``@app.route``, ``.path`` and ``.re_path``
* configure static site generation settings;
* set up distill URLs during conversion.
