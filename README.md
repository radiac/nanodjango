# nanodjango

[![PyPI](https://img.shields.io/pypi/v/nanodjango.svg)](https://pypi.org/project/nanodjango/)
[![Documentation](https://readthedocs.org/projects/nanodjango/badge/?version=latest)](https://nanodjango.readthedocs.io/en/latest/)
[![Tests](https://github.com/radiac/nanodjango/actions/workflows/ci.yml/badge.svg)](https://github.com/radiac/nanodjango/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/radiac/nanodjango/branch/main/graph/badge.svg?token=BCNM45T6GI)](https://codecov.io/gh/radiac/nanodjango)

Write a Django site in a single file, using views, models and admin, then automatically
convert it to a full Django project when you're ready for it to grow.

Perfect for experiments, prototypes, tutorials, and small applications.


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

app = Django(ADMIN_URL="admin/")

@app.admin
class CountLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)

@app.route("/")
def count(request):
    CountLog.objects.create()
    return f"<p>Number of page loads: {CountLog.objects.count()}</p>"
```

Save that as ``counter.py``, then set up your database and run it locally with:

```sh
nanodjango counter.py run makemigrations counter
nanodjango counter.py run migrate
nanodjango counter.py run createsuperuser
nanodjango counter.py run
```

It will create your database in a ``db.sqlite3`` file next to your ``counter.py``, with
the appropriate migrations in ``migrations/``.

Run it in production using WSGI:

```sh
gunicorn -w 4 counter:app
```

or convert it to a full Django project:

```sh
nanodjango counter.py convert /path/to/project --name=myproject
```

For more details, see

* [Getting started](https://nanodjango.readthedocs.io/en/latest/get_started.html)
* [Tutorial](https://nanodjango.readthedocs.io/en/latest/tutorial.html)
* [Full Documentation](https://nanodjango.readthedocs.io/en/latest/index.html)
* [Changelog](https://nanodjango.readthedocs.io/en/latest/changelog.html)
