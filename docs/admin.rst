=====
Admin
=====

Enable the admin site
=====================

In nanodjango the admin site is opt-in. To enable it, provide an ``ADMIN_URL`` in
your settings with the path to serve the admin site::

    app = Django(ADMIN_URL="admin/")

Note that ``nanodjango convert`` builds on top of the standard ``django-admin
startproject`` template, so the admin site will always be enabled after conversion,
using ``"admin/"`` if ``ADMIN_URL`` was not set.


Set up the database
===================

You will need to ``migrate`` before use, and you will want to add a superuser::

    nanodjango myapp.py run migrate
    nanodjango myapp.py run createsuperuser



Register a model
================

There is a helpful decorator to register a model with the admin site::

    @app.admin
    class CountLog(models.Model):
        timestamp = models.DateTimeField(auto_now_add=True)


You can pass ``ModelAdmin`` attributes as arguments to the decorator::

    @app.admin(list_display=["id", "timestamp"], readonly_fields=["timestamp"])
    class CountLog(models.Model):
        timestamp = models.DateTimeField(auto_now_add=True)


Custom ModelAdmin
=================

There is nothing special about the admin site in nanodjango - if your custom
``ModelAdmin`` is too complex to define using the decorator, you can register one using
the standard Django approach::

    from django.contrib import admin

    class CountLogAdmin(admin.ModelAdmin):
      list_display = ["id", "timestamp"]
      readonly_fields = ["timestamp"]

    admin.site.register(CountLog, CountLogAdmin)
