from django.urls import include, path

urlpatterns = [
    path("answering_gpt/", include("restapi.v1.answering_gpt.urls")),
]
