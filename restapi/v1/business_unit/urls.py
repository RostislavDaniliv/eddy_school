from django.urls import path

from restapi.v1.business_unit import views

urlpatterns = [
    path('create/', views.BusinessUnitCreate.as_view(), name='businessunit-create'),
    path('update/<int:pk>/', views.BusinessUnitUpdateAPIView.as_view(), name='businessunit-update'),
    path('suspend/<int:pk>/', views.SuspendBusinessUnit.as_view(), name='businessunit-suspend'),
]
