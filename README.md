# nanodjango

[![PyPI](https://img.shields.io/pypi/v/nanodjango.svg)](https://pypi.org/project/nanodjango/)
[![Documentation](https://readthedocs.org/projects/nanodjango/badge/?version=latest)](https://nanodjango.readthedocs.io/en/latest/)
[![Tests](https://github.com/radiac/nanodjango/actions/workflows/ci.yml/badge.svg)](https://github.com/radiac/nanodjango/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/radiac/nanodjango/branch/main/graph/badge.svg?token=BCNM45T6GI)](https://codecov.io/gh/radiac/nanodjango)

Write a Django site in a single file, using views, models and admin, then automatically
convert it to a full Django project when you're ready for it to grow.

An alternative to Flask (see example below) and FastAPI (with django-ninja support built
in) - similar simple syntax, but with full access to Django's features such as the ORM,
auth and admin site.

Perfect for experiments, prototypes, sharing working code samples, and deploying small
production applications.


## Quickstart


Install nanodjango:

```sh
pip install nanodjango
```

Create a file ``counter.py`` using Django's standard features, and the ``@app.route``
and ``@app.admin`` decorators to tell nanodjango where your URLs, views and model admin
are:

```python

from django.db import models
from nanodjango import Django

app = Django()

@app.admin
class CountLog(models.Model):
    # Standard Django model, registered with the admin site
    timestamp = models.DateTimeField(auto_now_add=True)

@app.route("/")
def count(request):
    # Standard Django function view
    CountLog.objects.create()
    return f"<p>Number of page loads: {CountLog.objects.count()}</p>"

@app.api.get("/add")
def count(request):
    # Django Ninja API
    CountLog.objects.create()
    return {"count": CountLog.objects.count()}
```

Save that as ``counter.py``, then set up your database and run it locally with:

```sh
nanodjango start counter.py
```

It will create your database in a ``db.sqlite3`` file next to your ``counter.py``, with
the appropriate migrations in ``migrations/``, and serve your static and media files.
Alternatively you could run each of these commands manually with the ``run`` command, eg
``nanodjango run counter.py runserver 0:8000``

Run it in production using WSGI:

```sh
gunicorn -w 4 counter:app
```

or automatically convert it to a full Django project:

```sh
nanodjango convert counter.py /path/to/project --name=myproject
```

and with a [couple of extra
lines](https://nanodjango.readthedocs.io/en/latest/management.html#run-script), run the
development server as a standalone script using ``python``, or use ``pipx run`` to run
it and automatically install dependencies to a temporary virtual environment:

```sh
# Either
python script.py
# or
pipx run ./script.py
```

For more details, see

* [Getting started](https://nanodjango.readthedocs.io/en/latest/get_started.html)
* [Tutorial](https://nanodjango.readthedocs.io/en/latest/tutorial.html)
* [Full Documentation](https://nanodjango.readthedocs.io/en/latest/index.html)
* [Changelog](https://nanodjango.readthedocs.io/en/latest/changelog.html)
* [Examples](https://github.com/radiac/nanodjango/tree/main/examples) including how to
  use nanodjango with Django Ninja