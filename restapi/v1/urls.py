from django.urls import include, path

urlpatterns = [
    path("answering_gpt/", include("restapi.v1.answering_gpt.urls")),
    path("business_unit/", include("restapi.v1.business_unit.urls")),
    path("document/", include("restapi.v1.document.urls")),
]
