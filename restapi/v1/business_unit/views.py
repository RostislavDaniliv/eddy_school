from django.http import JsonResponse
from rest_framework import generics
from rest_framework.response import Response

from business_units.models import BusinessUnit
from .decorators import apikey_required
from .serializers import BusinessUnitSerializer


class BusinessUnitCreate(generics.CreateAPIView):
    queryset = BusinessUnit.objects.all()
    serializer_class = BusinessUnitSerializer


class BusinessUnitUpdateAPIView(generics.UpdateAPIView):
    queryset = BusinessUnit.objects.all()
    serializer_class = BusinessUnitSerializer

    @apikey_required
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        data = request.data

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @apikey_required
    def delete(self, instance, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return JsonResponse({'message': 'Business unit deleted successfully'}, status=204)


class SuspendBusinessUnit(generics.UpdateAPIView):
    queryset = BusinessUnit.objects.all()

    @apikey_required
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        data = request.data

        instance.is_active = data.get('is_active', True)
        instance.save()

        return JsonResponse({'is_active': instance.is_active})
