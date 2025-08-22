=============
Template Tags
=============

Nanodjango provides a template tag library that lets you define custom template tags and filters in your single-file application. These work just like Django's built-in template tags and are automatically converted to a proper Django template tag library when you convert your app to a full project.

Template tags are accessed through the ``app.templatetag`` property, which provides decorators for different types of template functionality.

Simple Tags and Block Tags
==========================

Simple tags process arguments and return a string. Block tags (new in Django 5.2) process content between opening and closing tags.

.. code-block:: python

    @app.templatetag.simple_tag
    def format_price(value):
        return f"${value:.2f}"

    @app.templatetag.simple_block_tag
    def upper_block(content):
        return content.upper()

Use in templates:

.. code-block:: html+django

    {% load myapp %}
    {% format_price 19.99 %}
    {% upper_block %}hello world{% endupper_block %}

Both support context access and custom names:

.. code-block:: python

    @app.templatetag.simple_tag(takes_context=True, name="greeting")
    def greet_tag(context, name):
        user = context.get('user', 'anonymous')
        return f"Hello {name} from {user}!"

    @app.templatetag.simple_block_tag(takes_context=True)
    def repeat_block(context, content, times=2):
        return content * int(times)

Template Filters
================

Template filters transform values in templates using the pipe ``|`` syntax.

.. code-block:: python

    @app.templatetag.filter
    def upper_first(value):
        """Uppercase the first character"""
        return value[0].upper() + value[1:] if value else ""

Use in templates:

.. code-block:: html+django

    {% load myapp %}
    {{ "hello world"|upper_first }}
    <!-- Output: Hello world -->

Custom Filter Names
-------------------

You can specify a custom name for your filter:

.. code-block:: python

    @app.templatetag.filter(name="shout")
    def exclaim_filter(value):
        return f"{value}!"

.. code-block:: html+django

    {{ "hello"|shout }}
    <!-- Output: hello! -->

Inclusion Tags
==============

Inclusion tags render a template with context data and include the result in the current template.

.. code-block:: python

    @app.templatetag.inclusion_tag("user_info.html")
    def show_user(user):
        return {
            'user': user,
            'is_staff': user.is_staff if user else False
        }

The template:

.. code-block:: html+django

    <!-- user_info.html -->
    <div class="user-info">
        {% if user %}
            <span>{{ user.username }}</span>
            {% if is_staff %}<badge>Staff</badge>{% endif %}
        {% else %}
            <span>Anonymous</span>
        {% endif %}
    </div>

Use in templates:

.. code-block:: html+django

    {% load myapp %}
    {% show_user request.user %}

Advanced Tags
=============

For complex template tags that need to parse custom syntax, use the ``@app.templatetag.tag`` decorator:

.. code-block:: python

    from django.template import Node

    class RepeatNode(Node):
        def __init__(self, count, content):
            self.count = count
            self.content = content

        def render(self, context):
            return self.content * self.count

    @app.templatetag.tag
    def repeat(parser, token):
        """Repeat text a specified number of times"""
        try:
            tag_name, count, content = token.split_contents()
            count = int(count)
            content = content.strip('"\'')
        except ValueError:
            raise template.TemplateSyntaxError(
                f"{token.contents.split()[0]} requires exactly 2 arguments"
            )
        return RepeatNode(count, content)

Use in templates:

.. code-block:: html+django

    {% repeat 3 "Hello! " %}
    <!-- Output: Hello! Hello! Hello!  -->

Loading Template Tags
=====================

In your templates, load your custom tags using the app name:

.. code-block:: html+django

    {% load myapp %}
    {% format_price 19.99 %}
    {{ "hello"|upper_first }}

Example App
===========

Here's a complete example showing various template tag types:

.. code-block:: python

    from nanodjango import Django

    app = Django()

    @app.templatetag.simple_tag
    def format_price(value):
        return f"${value:.2f}"

    @app.templatetag.simple_block_tag
    def upper_block(content):
        return content.upper()

    @app.templatetag.filter
    def upper_first(value):
        return value[0].upper() + value[1:] if value else ""

    @app.templatetag.simple_tag(takes_context=True)
    def greeting(context, name):
        user = context.get('user')
        if user and hasattr(user, 'username'):
            return f"Hello {name}, welcome back {user.username}!"
        return f"Hello {name}!"

    @app.route("/")
    def hello_world(request):
        return app.render(request, "hello.html", context={
            "name": "world",
            "price": 19.99,
            "user": request.user
        })

    app.templates = {
        "hello.html": """
    <!DOCTYPE html>
    <html>
    <head><title>Template Tags Example</title></head>
    <body>
        {% load myapp %}
        <h1>{% greeting name %}</h1>
        <p>Name: {{ name|upper_first }}</p>
        <p>Price: {% format_price price %}</p>
    </body>
    </html>
        """.strip(),
    }

Conversion to Django
====================

When you convert your nanodjango app to a full Django project using ``nanodjango convert``, your template tags are automatically converted to a proper Django template tag library:

- A ``templatetags/`` directory is created in your app
- A ``templatetags/myapp.py`` module is generated containing your template tag functions
- The module includes all necessary imports and Django Library registration
- Your template syntax remains exactly the same

This means you can develop with nanodjango's simple syntax and seamlessly transition to a full Django project when needed.

API Reference
=============

``app.templatetag.simple_tag(func=None, takes_context=None, name=None)``
    Register a callable as a simple template tag that processes arguments and returns a string.

``app.templatetag.filter(name=None, filter_func=None, **flags)``
    Register a callable as a template filter that transforms values using pipe syntax.

``app.templatetag.inclusion_tag(filename, func=None, takes_context=None, name=None)``
    Register a callable as an inclusion tag that renders a template with context data.

``app.templatetag.tag(name=None, compile_function=None)``
    Register a compilation function as a template tag for complex custom syntax parsing.