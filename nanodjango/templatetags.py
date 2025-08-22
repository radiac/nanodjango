"""
Template tag support for nanodjango single-file apps
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from django.template import Library

if TYPE_CHECKING:
    from .app import Django


class TemplateTagLibrary:
    """
    Template tag library for nanodjango apps.

    Provides the same API as Django's Library class but integrates with
    nanodjango's single-file architecture and conversion system.
    """

    def __init__(self, app: Django):
        self.app = app
        self._library = Library()

        # Store registered template tags/filters for conversion
        # List of (decorator_name, func, kwargs) tuples
        self._registered: list[tuple[str, Callable, dict]] = []

    @property
    def library(self) -> Library:
        """Access to the underlying Django Library instance"""
        return self._library

    def simple_tag(self, func=None, takes_context=None, name=None):
        """
        Register a callable as a simple template tag.

        Usage:
            @app.templatetag.simple_tag
            def my_tag(value):
                return f"Processed: {value}"
        """

        def decorator(func):
            kwargs = {
                k: v
                for k, v in {"takes_context": takes_context, "name": name}.items()
                if v is not None
            }

            self._registered.append(("simple_tag", func, kwargs))
            return self._library.simple_tag(
                func, takes_context=takes_context, name=name
            )

        if func is None:
            return decorator
        return decorator(func)

    def inclusion_tag(self, filename, func=None, takes_context=None, name=None):
        """
        Register a callable as an inclusion template tag.

        Usage:
            @app.templatetag.inclusion_tag('my_template.html')
            def my_inclusion_tag(value):
                return {'value': value}
        """

        def decorator(func):
            kwargs = {
                k: v
                for k, v in {
                    "filename": filename,
                    "takes_context": takes_context,
                    "name": name,
                }.items()
                if v is not None
            }

            self._registered.append(("inclusion_tag", func, kwargs))
            return self._library.inclusion_tag(
                filename, takes_context=takes_context, name=name
            )(func)

        if func is None:
            return decorator
        return decorator(func)

    def filter(self, name=None, filter_func=None, **flags):
        """
        Register a callable as a template filter.

        Usage:
            @app.templatetag.filter
            def my_filter(value):
                return value.upper()
        """

        def decorator(func):
            kwargs = {}
            if isinstance(name, str):
                kwargs["name"] = name
            kwargs.update(flags)

            self._registered.append(("filter", func, kwargs))
            if isinstance(name, str):
                return self._library.filter(name, func, **flags)
            else:
                return self._library.filter(func, **flags)

        if name is None and filter_func is None:
            return decorator
        elif name is not None and filter_func is None:
            if callable(name):
                return decorator(name)
            else:

                def named_decorator(func):
                    return self.filter(name, func, **flags)

                return named_decorator
        else:
            return decorator(filter_func)

    def simple_block_tag(self, func=None, takes_context=None, name=None):
        """
        Register a callable as a simple block template tag (Django 5.2+).

        Block tags can process content between opening and closing tags.

        Usage:
            @app.templatetag.simple_block_tag
            def upper_block(content):
                return content.upper()

            In template:
            {% upper_block %}hello world{% endupper_block %}
        """

        def decorator(func):
            kwargs = {
                k: v
                for k, v in {"takes_context": takes_context, "name": name}.items()
                if v is not None
            }

            self._registered.append(("simple_block_tag", func, kwargs))
            return self._library.simple_block_tag(
                func, takes_context=takes_context, name=name
            )

        if func is None:
            return decorator
        return decorator(func)

    def tag(self, name=None, compile_function=None):
        """
        Register a compilation function as a template tag.

        Usage:
            @app.templatetag.tag
            def my_complex_tag(parser, token):
                # Parse and return a Node
                pass
        """

        def decorator(func):
            kwargs = {}
            if isinstance(name, str):
                kwargs["name"] = name

            self._registered.append(("tag", func, kwargs))
            if isinstance(name, str):
                return self._library.tag(name)(func)
            else:
                return self._library.tag(func)

        if name is None and compile_function is None:
            return decorator
        elif name is not None and compile_function is None:
            if callable(name):
                return decorator(name)
            else:

                def named_decorator(func):
                    return self.tag(name, func)

                return named_decorator
        else:
            return decorator(compile_function)
