from django_flasky import Django


app = Django()


@app.route("/")
def hello_world(request):
    return "<p>Hello, World!</p>"
