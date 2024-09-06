=========
Changelog
=========

0.8.0 - TBC
-----------

Feature:

* Async support

Changes

* Adds ``uvicorn`` as a dependency for ease of use

Bugfix:

* Fixed issue where scripts without models could fail on ``migrate``
* Fixed issue where the app may not fully initialise when run as WSGI


0.7.1 - 2024-06-25
------------------

Feature:

* Serve static and media by default (#9)
* Support ``name`` argument in ``@app.route`` (#11)


0.7.0 - 2024-06-19
------------------

Feature:

* Embed support for django-ninja through the ``@app.api`` decorator. (#7)

Changes:

* New ``build_app_api`` and ``build_app_api_done`` plugin hooks


0.6.1 - 2024-06-14
------------------

Bugfix:

* Fix remaining hard-coded references to ``app`` in user source, update ``scale.py`` to
  use ``django`` instead of ``app`` to test. (#8)


0.6.0 - 2024-05-17
------------------

Feature:

* Add ``start`` command to create and initialise the database

Thanks to:

* Chris Beaven (SmileyChris) for suggesting a lower effort start (#4)
* Lincoln Loop for supporting this release


0.5.0 - 2024-05-14
------------------

Feature:

* Support regular expression paths and path includes
* Add plugin system to the converter for third-party extensions
* Add django-ninja converter plugin for ``NinjaAPI`` and example
* Add docs for writing converter plugins

Changes:

* Command line argument order has changed from ``<script> <cmd>`` to ``<cmd> <script>``
* Script can now be specified as a module, eg ``foo`` instead of ``foo.py``
* Django instance no longer needs to be ``app`` - its name can be specified as
  ``<script>:<name>`` (eg ``counter:myapp`` or ``counter.py:myapp``), or can be
  auto-detected.
* ``ADMIN_URL`` is now optional - the admin site will be enabled if there are any admin
  decorators present

Internal:

* Remove redundant cleaning of leading slash in paths
* Improved gitignore

Thanks to:

* Eric Matthes (ehmatthes) for removing the redundant cleaning of the leading slash,
  improving the gitignore (#2), and rewriting the contributor docs (#3)
* Chris Beaven (SmileyChris) for suggesting the command line changes (#5)


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
