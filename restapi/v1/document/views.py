from django.http import JsonResponse
from rest_framework import generics
from rest_framework.response import Response

from business_units.models import Document
from restapi.v1.document.serializers import DocumentSerializer


class DocumentCreate(generics.CreateAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class DocumentAPIView(generics.UpdateAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        data = request.data

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def delete(self, instance, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return JsonResponse({'message': 'Business unit deleted successfully'}, status=204)
