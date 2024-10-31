import inspect

from django.http import HttpResponse


def string_view(fn):
    """
    Wrapper to automatically convert the response from a view function into an
    HttpResponse to support returning a string.
    """
    if inspect.iscoroutinefunction(fn):

        async def django_view(request, **kwargs):
            response = await fn(request)
            if isinstance(response, HttpResponse):
                return response
            return HttpResponse(response)
    else:

        def django_view(request, **kwargs):
            response = fn(request, **kwargs)
            if isinstance(response, HttpResponse):
                return response
            return HttpResponse(response)

    return django_view
