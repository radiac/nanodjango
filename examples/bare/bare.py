"""
nanodjango - Bare mode example

A minimal app with no database, using cookie-based sessions and messages.

Usage::

    nanodjango run bare.py
"""

from django.contrib import messages

from nanodjango import Django

app = Django(BARE=True)


@app.route("/")
def index(request):
    # Test sessions work
    count = request.session.get("count", 0) + 1
    request.session["count"] = count
    return f"<p>Visit count: {count}</p>"


@app.route("/message/")
def add_message(request):
    # Test messages work
    messages.success(request, "Hello from bare mode!")
    return "<p>Message added</p>"


@app.route("/show-messages/")
def show_messages(request):
    # Get messages from the request
    msg_list = [str(m) for m in messages.get_messages(request)]
    return f"<p>Messages: {msg_list}</p>"
