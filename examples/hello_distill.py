"""
Hello world, with django-distill support
"""

from nanodjango import Django

app = Django()


@app.route("/", distill=True)
def hello_world(request):
    return "<p>Hello, World!</p>"
