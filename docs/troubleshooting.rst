===============
Troubleshooting
===============

Because nanodjango is performing some trickery to run everything from one file, you may
occasionally run into an issue.


Settings are not configured
===========================

Sample error message::

    django.core.exceptions.ImproperlyConfigured: Requested setting DEBUG, but settings are not configured.

When running your script directly (``python counter.py``), Django is configured during
``from nanodjango import Django``, so this error is unlikely to occur.

However, when running via CLI (``nanodjango run counter.py``), Django is configured later.
If you see this error, something is trying to access a Django setting before Django is
configured.

This can usually be fixed with :doc:`defer`.
