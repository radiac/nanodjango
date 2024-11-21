# Will be populated at runtime
from django.urls.resolvers import URLPattern, URLResolver
import djp


urlpatterns: list[URLPattern | URLResolver] = djp.urlpatterns()
