=======================
Extending the converter
=======================

Code for third party libraries may not be put in the right place by the standard
conversation process - for example, by default a django-ninja ``@api.get(..)`` function
will not be recognised as a view, so will end up in ``unused.py``.

To avoid this, nanodjango has a converter plugin system. If you are a library maintainer
who wants to control their part of the conversion process, the converter can be released
as part of the library; if you are a library user, you can either release your own
package, or suggest it as a candidate to be shipped with nanodjango as part of
``nanodjango.convert.contrib``.


Using your plugin
=================

Using locally
-------------

During development, or if you don't plan on distributing your plugin, you can tell
nanodjango about plugin modules with the ``convert --plugin=<path>`` argument::


    nanodjango app.py convert project --name=example --plugin=myplugin.py

This will import ``app.py``, then ``myplugin .py`` to register any plugins, then start
the conversion process.

Because plugins are automatically registered when they're imported, you could also
import or define them in your ``app.py``.


Distributing the plugin
-----------------------

If you are distributing the plugin yourself, you can have nanodjango detect it
automatically by adding an entry point for it.

If your project is called ``myproject``, put the plugin in a file in your project (it
recommended name is ``nanodjango.py``, but could be anything), then specify its dot path
in the entry point.


setup.py::

    setup(
        ...
        entry_points={
            "nanodjango": [
                "myproject = myproject.nanodjango"
            ]
        },
    )

pyproject.toml::

    [project.entry-points.nanodjango]
    myproject = "myproject.nanodjango"


Any converter plugins defined in that file will be detected.


Writing a plugin
================

Your plugin should subclass ``nanodjango.convert.plugin.ConverterPlugin``.

* This will automatically register your plugin once it has been imported.
* Plugins will run in the order they are imported; this could vary, so ensure plugins
  are independent.
* Plugin methods are called throughout the conversion process, allowing you to hook in
  and claim or modify objects, or otherwise modify the generated files.
* All methods receive the current ``Converter`` instance as the first argument.
* Some methods have additional positional arguments. Those should be returned in the
  same order, and will be passed on to the next plugin, or back to the originating
  function.

If you find you need a new hook or that an existing hook doesn't work for you, please do
submit an issue or PR.


Tutorial
--------

nanodjango comes with plugins for common third-party libraries, including
``django-ninja``. We'll build that again to see how it's done.


Create the plugin
~~~~~~~~~~~~~~~~~

Using Ninja with nanodjango looks something like this::

    from ninja import NinjaAPI
    api = NinjaAPI()

    @api.get("/add")
    def add(request, a: int, b: int):
        return {"result": a + b}

    app.route("api/", include=api.urls)

The converter will recognise the route and put that in our new ``urls.py``, and will
know that it references ``api``, which in turns references ``NinjaAPI``, and they will
go into ``urls.py`` where they're needed for the url path.

However, the converter won't be sure what to do with the ``@api.get(..)`` decorator,
because that's not required by the route definition. That will end up in ``unused.py``
in our new app, but we want it all in ``api.py``, as is Django Ninja convention.

For that we need to write a plugin.

Lets create a new plugin file, ``django_ninja.py``, and subclass the
``ConverterPlugin``. Building our ``api.py`` after we've built ``models.py`` seems like
a sensible time, so we'll use the ``build_app_models_done`` hook::

    class NinjaConverter(ConverterPlugin):
        def build_app_models_done(self, converter: Converter):
            ...

This will automatically register the plugin once the file is imported, and our method
will be called after the ``models.py`` has been built.

We're passed the ``converter`` instance - this keeps track of the originating source
code, and which symbols have been converted up to this point.

If you've not worked with Python's abstract syntax trees before, now would be a good
time to have a quick skim of the `AST module documentation
<https://docs.python.org/3/library/ast.html>`_ - but you can get by using the helper
function ``nanodjango.convert.utils.pp_ast`` to pretty print the AST object structure as
you go.


Find NinjaAPI instances
~~~~~~~~~~~~~~~~~~~~~~~

We now want to find all ``NinjaAPI`` instances.

We will go through the root level of the app's AST (its globals), looking for a
definition of a ``NinjaAPI`` instance. Using ``pp_ast(converter.ast.body)`` on
``examples/ninja_api.py``, we can see it will look something like::

    Assign(
    targets=[
      Name(id='api', ctx=Store())],
    value=Call(
      func=Name(id='NinjaAPI', ctx=Load()),
      args=[],
      keywords=[]))

The title-cased items there (``Assign``, ``Call`` etc) are instances of ``ast`` classes,
so you can see we've found an ``ast.Assign`` assignment, into the variable name ``api``,
and the value we're assigning is the result of an ``ast.Call`` to ``NinjaAPI`` - in
other words, ``api`` is going to be an instance of ``NinjaAPI``.

Before we start looking, we're going to create a ``Resolver(converter, ".api")``
instance to keep track of symbols we're claiming for our file. That needs access to the
current ``converter``, and also the name of the module we're going to be putting our
symbols in, relative to other files in our app - so because we're writing to ``api.py``,
it will be ``.api``.

We'll also make an ``api_objs = set()`` to keep track of which ``NinjaAPI`` instances
we've found, and a ``code`` list to store the code we want in ``api.py``.

Putting all this together, we get::

    import ast
    from nanodjango.convert.plugin import ConverterPlugin, Resolver

    class NinjaConverter(ConverterPlugin):
        def build_app_models_done(self, converter: Converter):
            resolver = Resolver(converter, ".api")
            api_objs = set()
            code = []

            for obj_ast in converter.ast.body:
                if (
                    isinstance(obj_ast, ast.Assign)
                    and isinstance(obj_ast.value, ast.Call)
                    and isinstance(obj_ast.value.func, ast.Name)
                    and obj_ast.value.func.id == "NinjaAPI"
                ):
                    # We've found a NinjaAPI instance

It could be assigned to multiple targets, so now we've found it, lets loop over its
targets and register them with our set and the resolver::

    from nanodjango.convert.utils import collect_references
    ...
                if (...):
                    for target in obj_ast.targets:
                        if isinstance(target, ast.Name):
                            name = target.id
                            api_objs.add(name)
                            references = collect_references(obj_ast)
                            resolver.add(name, references)
                            src = ast.unparse(obj_ast)
                            code.append(src)

Here we also used ``collect_references`` to find out which other symbols in our app this
definition needs - in most cases this will just be a reference to ``NinjaAPI``. We pass
these into the resolver so it can track them down later.


Find endpoints
~~~~~~~~~~~~~~

That's the ``NinjaAPI`` instance found, now for the endpoint functions it decorates.

Using ``pp_ast`` again, the AST object for a decorated function will look like this::

    FunctionDef(
      name='add',
      args=arguments(...),
      body=[...],
      decorator_list=[
        Call(
          func=Attribute(
            value=Name(id='api', ctx=Load()),
            attr='get',
            ctx=Load()),
          args=[
            Constant(value='/add')],
          keywords=[])])

You will notice it's an ``ast.FunctionDef``, and that it has a ``decorator_list`` which
mentions ``api``, one of the ``NinjaAPI`` instances we found previously. That should be
enough to add to our loop. Lets also use the ``get_decorators`` helper from
``nanodjango.convert.utils``:

    from nanodjango.convert.utils import get_decorators
    ...
            elif isinstance(obj_ast, ast.FunctionDef):
                decorators = get_decorators(obj_ast)
                for decorator in decorators:
                    # If it's been used as ``@decorator()`` then there's a function call
                    # - if it was ``@decorator`` there won't. Standardise to make it
                    # easier to work with
                    if isinstance(decorator, ast.Call):
                        decorator = decorator.func

                    if (
                        isinstance(decorator, ast.Attribute)
                        and isinstance(decorator.value, ast.Name)
                        and decorator.value.id in api_objs
                    ):
                        resolver.add_object(obj_ast.name)
                        references = collect_references(obj_ast)
                        resolver.add(name, references)
                        src = ast.unparse(obj_ast)
                        code.append(src)

Once we've found a decorator using one of the ``api_objs`` symbols we found earlier, we
can be pretty sure it's a Ninja endpoint - so we again collect anything it references,
register it with the resolver, and store its source code.

We've duplicated some logic there, so the final version splits ``resolver.add`` into
``resolver.add_object`` and ``resolver.add_references`` - but this will work.


Write the file
~~~~~~~~~~~~~~

Now we've collected all the necessary references and source, we can generate our file::


        def build_app_models_done(self, converter: Converter):
            ...
            if not api_objs:
                return

            converter.write_file(
                converter.app_path / "api.py",
                resolver.gen_src(),
                "\n".join(code),
            )

First we check ``if not api_objs`` - remember this may be active in projects that aren't
using django-ninja, so if we didn't find any NinjaAPI definitions, then we're not going
to have anything to write to ``api.py``.

But if we did, get the converter to write into ``api.py`` in the app dir. We're using
``converter.write_file`` which takes the filename and the lines to write, and then
applies black and isort to tidy our code.

First we're going to write ``resolver.gen_src()``. Remember we told the resolver the
symbols our code referenced? Now it's able to go away build the code it needs to get
those symbols into our file - that may mean importing models from ``models.py``,
importing third party objects such as ``NinjaAPI``, or just copying in code that hasn't
been used before now - eg if we'd referenced a global variable or helper function.

Lastly we write the code we found interesting - the ``NinjaAPI`` instantiations and
decorated endpoint functions.

Note that we didn't do anything with the ``app.route("api/", include=api.urls)`` call -
we want that to go into ``urls.py`` so that's the responsibility of the
``build_app_urls`` method. That's going to find the route, and it's going to tell its
resolver it needs to find ``api`` - then when ``urls.py`` writes out its
``resolver.gen_src()``, the urls will get a ``from .api import api``.
