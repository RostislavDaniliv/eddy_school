from django.urls import include, path
from rest_framework_swagger.views import get_swagger_view

from eddy_school.yasg import urlpatterns as doc_urls

schema_view = get_swagger_view(title='Eddy School API')

urlpatterns = [
    path("1.0/", include("restapi.v1.urls")),
]

urlpatterns += doc_urls
