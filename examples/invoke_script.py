from nanodjango import Django

app = Django()


@app.route("/")
def index(request):
    return "Hello from invoke"


if __name__ == "__main__":
    app.invoke(default="manage check")
