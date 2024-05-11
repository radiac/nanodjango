=========
Changelog
=========

0.5.0 - ???
-----------

Feature:

* Support regular expression paths and path includes
* Add plugin system to the converter for third-party extensions
* Add django-ninja converter plugin for ``NinjaAPI`` and example
* Add docs for writing converter plugins

Internal:

* Remove redundant cleaning of leading slash in paths
* Improved gitignore

Thanks to:

* Eric Matthes (ehmatthes) for removing the redundant cleaning of the leading slash,
  improving the gitignore, and rewriting the contributor docs


0.4.0 - 2024-04-21
------------------

Feature:

* Add support for CBVs
* Add support for running management commands from within a script
* WSGI mode now runs with ``DEBUG=False`` by default
* Document usage with ``pipx run``

Bugfix

* Fix template path


0.3.0 - 2024-04-14
------------------

Feature:

* Add ``convert`` command to turn a single file app into a full Django project
* Add settings ``EXTRA_APPS``, ``SQLITE_DATABASE`` and ``MIGRATIONS_DIR``
* Add WSGI support
* Rename project from ``django-flasky``


0.2.0 - 2024-04-01
------------------

Feature:

* Admin support
* Add setting ``ADMIN_URL``


0.1.3 - 2023-10-19
------------------

Fix:

* Python compatibility issue in run command



0.1.2 - 2022-11-25
------------------

Docs:

* Correct examples


0.1.1 - 2022-11-25
------------------

Docs:

* Correct packaging metadata



0.1.0 - 2022-11-25
------------------

Initial release as ``django-flasky``
