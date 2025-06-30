===============
Troubleshooting
===============

Because nanodjango is performing some trickery to run everything from one file, you may
occasionally run into an issue.


Settings are not configured
===========================

Sample error message::

    django.core.exceptions.ImproperlyConfigured: Requested setting DEBUG, but settings are not configured.

You will see this when something is trying to access a Django setting before you've
called ``app = Django()`` to configure Django.

This can usually be fixed with :doc:`defer`.
