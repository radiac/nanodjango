"""
nanodjango - Django models, views and admin in a single file

Embedded template example

Usage::

    nanodjango run hello_template.py
    nanodjango convert hello_template.html /path/to/site --name=myproject
"""

from nanodjango import Django

app = Django(
    # Avoid clashes with other examples
    SQLITE_DATABASE="hello_template.sqlite3",
    MIGRATIONS_DIR="hello_template_migrations",
)


@app.route("/")
def hello_world(request):
    return app.render(request, "hello.html", context={"message": "Hello!"})


app.templates = {
    "base.html": "<html><body><h1>Base title</h1>{% block content %}{% endblock %}</body></html>",
    "hello.html": "{% extends 'base.html' %}{% block content %}<p>Hello, World!</p>{% endblock %}",
}
