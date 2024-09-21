# nanodjango

[![PyPI](https://img.shields.io/pypi/v/nanodjango.svg)](https://pypi.org/project/nanodjango/)
[![Documentation](https://readthedocs.org/projects/nanodjango/badge/?version=latest)](https://nanodjango.readthedocs.io/en/latest/)
[![Tests](https://github.com/radiac/nanodjango/actions/workflows/ci.yml/badge.svg)](https://github.com/radiac/nanodjango/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/radiac/nanodjango/branch/main/graph/badge.svg?token=BCNM45T6GI)](https://codecov.io/gh/radiac/nanodjango)

* Write a Django site in a single file, using views, models and admin
* Run it locally or in production, or share it as a standalone script
* Automatically convert it to a full Django project when you're ready for it to grow


## Quickstart

Install nanodjango:

```sh
pip install nanodjango
```

Write your app in single `.py` file - for example:

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
def add(request):
    # Django Ninja API support built in
    CountLog.objects.create()
    return {"count": CountLog.objects.count()}

@app.route("/slow/")
async def slow(request):
    import asyncio
    await asyncio.sleep(10)
    return "Async views supported"
```

Save that as `counter.py`, then set it up and run it:

```sh
nanodjango run counter.py
```

This will create migrations and a database, and run your project in development mode.

* See [Command usage](https://nanodjango.readthedocs.io/en/latest/usage.html)
  for more options

### Convert it to a full site

If your project outgrows its single file, you can convert it into a full Django site:

```sh
nanodjango counter.py convert path/to/site --name=counter
```

* See
  [Converting to a full Django project](https://nanodjango.readthedocs.io/en/latest/convert.html)
  for more information


### Share an app

Nanodjango apps are great for sharing examples and prototypes.

Add [inline script metadata](https://peps.python.org/pep-0723/) at the top with your
dependencies:

```python
# /// script
# dependencies = ["nanodjango"]
# ///
```

and call `app.run()` at the bottom:

```python
if __name__ == "__main__":
    app.run()
```

Now your app can be run without installing anything, using `uv` or `pipx`:

```sh
# Run with uv
uv run ./script.py
# or with pipx
pipx run ./script.py
```

You can still manually install dependencies and run the script directly with Python:

```sh
pip install nanodjango
python script.py
```


### Run management commands

Anything you would normally do with `manage.py` you can do with `nanodjango manage`:
```sh
nanodjango manage script.py check
nanodjango manage script.py makemigrations script
nanodjango manage script.py runserver 0:8000
```


### Run in production

Run it using ``nanodjango serve``:
```sh
nanodjango serve counter.py
```

This will use gunicorn, or uvicorn if you have async views.

Alternatively, you can pass the app directly to a WSGI or ASGI server if you prefer:
```sh
gunicorn -w 4 counter:app
uvicorn counter:app
```
* See [Command usage](https://nanodjango.readthedocs.io/en/latest/usage.html)
  for more options

### Further reading

For more details, see

* [Getting started](https://nanodjango.readthedocs.io/en/latest/get_started.html)
* [Tutorial](https://nanodjango.readthedocs.io/en/latest/tutorial.html)
* [Full Documentation](https://nanodjango.readthedocs.io/en/latest/index.html)
* [Changelog](https://nanodjango.readthedocs.io/en/latest/changelog.html)
* [Examples](https://github.com/radiac/nanodjango/tree/main/examples)
