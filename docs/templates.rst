=========
Templates
=========

There are two ways to define templates for use with nanodjango apps:

* put them in a ``templates/`` dir next to your script
* define them on the ``app.templates`` dict

Whichever approach you take, you can render them using standard techniques, or the
``app.render`` shortcut method.


Defining templates
==================

To define a template in the same script as the rest of your code, assign the templates
to the ``app.templates`` dict, using the filename and relative path as the key, and the
template content as the value.

It is recommended that templates are defined at the bottom of your script, out of the
way of your code.

You can either assign by key:

.. code-block:: python

    app.templates["base.html"] = """<!doctype html>
      <html lang="en">
        <body>
          {% block content %}{% endblock %}
        </body>"
      </html>
    """
    app.templates["myview/hello.html"] = "{% block content %}Hello{% endblock %}"


or by dict:

.. code-block:: python

    app.templates = {
      "base.html": """<!doctype html>
        <html lang="en">
          <body>
            {% block content %}{% endblock %}
          </body>"
        </html>
      """,
      "myview/hello.html": """
          {% extends "base.html" %}
          {% block content %}Hello{% endblock %}
      """,
    }


This uses Django's ``locmem`` template loader, so these templates can be extended and
included as normal templates, and can work with files in a ``templates`` dir.

If a template path is defined as both a file and in the ``app.templates`` dict, the
template in the dict will be used.


Using templates
===============

Nanodjango provides a helper method to quickly render a template:
**app.render(__request, template_name, context=None, content_type=None, status=None,
using=None__)**

Example usage:

.. code-block:: python

    @app.route("/")
    def index(request):
        return app.render(request, "index.html", {"books": Book.objects.all()})

    app.templates = {
        "index.html" : """
            {% extends "base.html" %}
            {% block content %}
              <p>There are {{ books.count }} books:</p>
              {% for book in books %}
                <p>{{ book.title }}</p>
              {% endfor %}
            {% endblock %}
        """,
        ...
    }

This is a direct convenience wrapper for `django.shortcuts.render
<https://docs.djangoproject.com/en/dev/topics/http/shortcuts/#render>`. When converting
a script which calls ``app.render``, nanodjango will attempt to rewrite it to use the
standard Django shortcut.


Converting templates
====================

Running the ``nanodjango convert`` command on an app script will put templates in the
app's ``templates`` directory.

Files which are in a dir will be copied across.

Templates defined in the ``app.templates`` dict will be written out to files.

If the same template path is defined in both, the template from the dict will be written
to the file.
