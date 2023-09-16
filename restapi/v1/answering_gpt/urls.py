from django.urls import path

from restapi.v1.answering_gpt import views

urlpatterns = [
    path("", views.GPTAnswerView.as_view())
]
