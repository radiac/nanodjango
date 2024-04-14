from django.http import HttpResponse


def string_view(fn):
    """
    Wrapper to automatically convert the response from a view function into an
    HttpResponse to support returning a string.
    """

    def django_view(request):
        response = fn(request)
        if isinstance(response, HttpResponse):
            return response
        return HttpResponse(response)

    return django_view
