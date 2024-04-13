=====
Admin
=====

Add the admin site
==================

The admin site is opt-in.

To enable the admin site, set ``ADMIN_URL = "/path/"`` in your settings::

    app = Django(ADMIN_URL="admin/")


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

To define a custom ``ModelAdmin``, use standard Django syntax::

    from django.contrib import admin

    class CountLogAdmin(admin.ModelAdmin):
      list_display = ["id", "timestamp"]
      readonly_fields = ["timestamp"]

    admin.site.register(CountLog, CountLogAdmin)
