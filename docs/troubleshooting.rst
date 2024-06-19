===============
Troubleshooting
===============

Because nanodjango is performing some trickery to run everything from one file, you may
occasionally run into an issue:


Settings are not configured
===========================

Sample error message::

    django.core.exceptions.ImproperlyConfigured: Requested setting DEBUG, but settings are not configured.

You will see this when something is trying to access a Django setting before you've
called ``app = Django()`` - remember that you pass the settings into ``Django()``, so
settings won't be ready to use until then.

To solve this, change the order of your code so that the ``Django`` class is
defined *before* the code that performs the settings lookup.

For example this is an issue with django-ninja - it checks ``settings,DEBUG`` while
importing the library::

    from nanodjango import Django
    from ninja import NinjaAPI  # will fail here, settings are not configured
    app = Django()
    api = NinjaAPI()

we can fix this by moving the ninja import to after instantiating the ``Django`` class:

    from nanodjango import Django
    app = Django()

    from ninja import NinjaAPI  # will fail here, settings are not configured
    api = NinjaAPI()
