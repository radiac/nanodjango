from nanodjango import Django

app = Django()


@app.route("/")
def hello_world(request):
    return "<p>Hello, World!</p>"
