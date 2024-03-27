from django.urls import path

from restapi.v1.document import views

urlpatterns = [
    path('create/', views.DocumentCreate.as_view(), name='document-create'),
    path('update/<int:pk>/', views.DocumentAPIView.as_view(), name='document-update'),
]
