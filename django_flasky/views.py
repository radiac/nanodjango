from django.http import HttpResponse


def flask_view(fn):
    """
    Wrapper to automatically convert the response from a view function into an
    HttpResponse to match Flask's view syntax
    """

    def django_view(request):
        response = fn(request)
        return HttpResponse(response)

    return django_view
