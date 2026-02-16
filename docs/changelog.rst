=========
Changelog
=========

0.14.0 - TBC
------------

Features:

* Add settings callback support (#74, #77, #90)
* Automatic superuser creation and command line arguments (experimental, see #94)

Bugfix:

* Make runserver Windows-compatible (#45, #91)

Thanks to:

* D Chukhin (dchukhin) for early work on settings callbacks (#77)
* Chris Beaven (SmileyChris) for windows fix (#91), settings callbacks (#90)


0.13.0 - 2026-01-18
-------------------

Features:

* Add ``app.create_server()`` to run nanodjango as an async task (#68, #78), and
  ``examples/hello_async_server.py`` to demonstrate it.

Bugfix:

* Fix ``HttpResponseBase`` subclass support in ``string_view`` wrapper (#87)

Docs:

* Replaced theme
* Swapped to build using dirhtml for nicer urls
* Fixed uwsgi instructions (#58)
* Added :doc:`internal API docs <internal_api>`
* Added :doc:`API howto <howto_api>` (#70, #83)

Thanks to:

* Emmanuelle Delescolle (nanuxbe) for uwsgi fix (#58)
* Bryan Ponce (bponce02) for ``app.create_server()`` (#68, #78)
* Sadegh (Old6Man6) for API example and howto (#70, #83)
* Chris Beaven (SmileyChris) for ``string_view`` fix (#87)


0.12.2 - 2025-09-11
-------------------

Bugfix:

* Fixed module resolution error blocking scripts from running directly

Internal:

* Rename legacy ``DF_*`` settings to ``ND_*`` (#55)

Thanks to:

* Bryan Ponce (bponce02) for ``DF*`` fix (#55)



0.12.1 - 2025-09-01
-------------------

Bugfix:

* Fix convert AST unparsing errors by adding missing location information
* Extend convert import detection to recursively search within nested blocks
* Extend convert reference tracking for blocks (context manager, exception handlers) and tuple unpacking
* Add convert urlpatterns regex matching to support type hints in convert templates
* Fix convert decorator filtering to handle all route decorator types


0.12.0 - 2025-08-24
-------------------

Features:

* Django requirement now 5.2
* Add :doc:`template tags <template_tags>` support
* Add ``convert_build_app_templatetags`` and ``convert_build_app_templatetags_done``
  hooks
* Add ``django_browser_reload`` contrib plugin to support automatic browser reloading
* Add ``--template`` option to ``convert`` command for custom Django project templates
  (#42)

Docs:

* Add "Integrations" section to track growing list of key packages which either have
  ``nanodjango.contrib`` plugins or provide plugins themselves.

Bugfix:

* Fix arguments not being passed through in manage command (#61, #66)
* Fix issue with multiple deferred imports in a single statement
* Fix WSGI/ASGI preparation to avoid double initialization
* Fix missing ``urls`` argument in hook
* Improve patch migrations to work around missing migration dir in some environments


0.11.2 - 2025-07-06
-------------------

Bugfix:

* Fix defer issues by switching to using bytecode to detect import statements


0.11.1 - 2025-07-01
-------------------

Bugfix:

* Correct spelling of app.re_path


0.11.0 - 2025-06-30
-------------------

Features:

* Added support for :doc:`deferred imports <defer>`
* Added :doc:`new plugin system <plugins>` using pluggy
* Added contrib plugin for django-distill for support in ``Django.route()``.
* Added django-nanopages and django-distill as optional dependencies under ``[static]``
* Install all optional dependencies with ``[full]``
* Refactored test tools into ``nanodjango.tests.utils`` for third party tests
* Added ``Django.path()`` and ``Django.re_path()`` convenience methods

Breaking changes:

* The ``convert`` plugin system has been replaced with the pluggy-based plugin system -
  see :ref:`upgrade_0_11_0__plugins` below
* The ``--plugin`` option has moved from ``nanodjango convert --plugin=...`` to
  ``nanodjango --plugin=... <command>``
* Plugins are no longer registered on import - plugins now need to be added via
  setup hook, explicitly listed on the command line with ``--plugin``, or manually
  registered using ``app.pm.hook.register(...)``.

Bugs:

* Fix admin site URL priority so it is still served with a catch-all route.


.. _upgrade_0_11_0__plugins:

Upgrading convert plugins
~~~~~~~~~~~~~~~~~~~~~~~~~

Existing converter plugins will need to be converted to work with pluggy.

Code within plugin hooks should work as before, but they will need to be restructured.

#. remove imports from ``nanodjango.convert.plugins`` - that no longer exists
#. add ``from nanodjango import hookimpl``
#. remove the ``ConverterPlugin`` classes and move the methods to functions
#. add the ``@hookimpl`` decorator to the plugin functions
#. add a ``convert_`` prefix to the function names
#. You should use side effects to update args in place, like the resolver and extra_src

For example, if your plugin was::

    from ..convert.plugin import ConverterPlugin

    class MyConverter(ConverterPlugin):
        def build_app_api(
            self, converter: Converter, resolver: Resolver, extra_src: list[str]
        ) -> tuple[Resolver, list[str]]:
            # do something
            return resolver, extra_src

it should now be::

    from nanodjango import hookimpl

    @hookimpl
    def convert_build_app_api(
        converter: Converter, resolver: Resolver, extra_src: list[str]
    ):
        # update resolver and extra_src in place




0.10.0 - 2025-02-13
-------------------

Features:

* Support templates in the single file (#44)

Bugs:

* Add missing license file (#49)
* Fix view decorators when used with ``@app.route`` (#50)
* Fix incorrect convert command in readme (#53)
* Fix missing arguments in ``string_view`` (#54)

Thanks to:

* lybtt for the readme fix (#53)


0.9.2 - 2024-10-14
------------------

Bugs:

* Fix kwarg handling in string_view decorator (#31)

Docs:

* Fix incorrect tutorial syntax (#32, #33)

Thanks to:

* 최병욱 (esc5221) for providing the kwarg handling fix (#31)
* Abdulwasiu Apalowo (mrbazzan) for providing doc fix (#32, #33)


0.9.1 - 2024-09-27
------------------

Bugs:

* Fix instance name detection (#21, #22)
* Fix dev mode ASGI (#23)

Docs:

* Fix incorrect doc reference (#16)
* Fix incorrect tutorial syntax (#15, #16)
* Fix incorrect convert command invocation (#25)
* Fix incorrect troubleshooting syntax (#26)

Thanks to:

* Simon Willison (simonw) for providing doc fixes (#15, #16)
* vincent d warmerdam (koaning) for providing doc fixes (#26)


0.9.0 - 2024-09-21
------------------

Features:

* ``nanodjango serve`` command for production deployments
* Static files are now served using ``whitenoise``
* Serve static files in the site root from ``PUBLIC_DIR`` dir (default ``public``)

Breaking changes:

* ``nanodjango run`` is now ``nanodjango manage``, mirroring ``manage.py``.
* ``nanodjango manage`` no longer calls ``runserver`` by default.
* ``nanodjango start`` is now ``nanodjango run``, differentiating it from ``serve``.
* ``Django.run()`` is now ``Django.manage()``
* ``Django.start()`` is now ``Django.run()``


0.8.1 - 2024-09-07
------------------

Changes:

* Add async API detection for async endpoints registered with ``@app.api``


0.8.0 - 2024-09-07
------------------

Feature:

* Async support

Changes:

* Add ``uvicorn`` as a dependency for ease of use

Bugfix:

* Fix issue where scripts without models could fail on ``migrate``
* Fix issue where the app may not fully initialise when run as WSGI


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
