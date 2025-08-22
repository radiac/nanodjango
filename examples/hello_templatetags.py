"""
nanodjango - Template tags example

Usage::

    nanodjango run hello_templatetags.py
    nanodjango convert hello_templatetags.py /path/to/site --name=myproject
"""

from nanodjango import Django

app = Django(
    # Avoid clashes with other examples
    SQLITE_DATABASE="hello_templatetags.sqlite3",
    MIGRATIONS_DIR="hello_templatetags_migrations",
)


@app.templatetag.simple_tag
def format_price(value):
    """Format a price with dollar sign"""
    return f"${value:.2f}"


@app.templatetag.filter
def upper_first(value):
    """Uppercase the first character"""
    return value[0].upper() + value[1:] if value else ""


@app.templatetag.simple_tag(takes_context=True)
def greeting(context, name):
    """Generate a greeting using context"""
    user = context.get("user")
    if user and hasattr(user, "username"):
        return f"Hello {name}, welcome back {user.username}!"
    return f"Hello {name}!"


@app.route("/")
def hello_world(request):
    return app.render(
        request,
        "hello.html",
        context={
            "name": "world",
            "price": 19.99,
            "user": request.user if hasattr(request, "user") else None,
        },
    )


app.templates = {
    "hello.html": """
<!DOCTYPE html>
<html>
<head><title>Template Tags Example</title></head>
<body>
    {% load hello_templatetags %}
    <h1>{% greeting name %}</h1>
    <p>Name: {{ name|upper_first }}</p>
    <p>Price: {% format_price price %}</p>
</body>
</html>
""".strip(),
}
