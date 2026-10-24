from functools import wraps

from asgiref.sync import iscoroutinefunction
from django.http import HttpResponse, HttpResponseBase


def string_view(fn):
    """
    Wrapper to automatically convert the response from a view function into an
    HttpResponse to support returning a string.
    """
    if iscoroutinefunction(fn):

        @wraps(fn)
        async def django_view(request, *args, **kwargs):
            response = await fn(request, *args, **kwargs)
            if isinstance(response, HttpResponseBase):
                return response
            return HttpResponse(response)

    else:

        @wraps(fn)
        def django_view(request, *args, **kwargs):
            response = fn(request, *args, **kwargs)
            if isinstance(response, HttpResponseBase):
                return response
            return HttpResponse(response)

    return django_view
