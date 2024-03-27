from functools import wraps

from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response


def apikey_required(func):
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        instance = self.get_object()
        apikey = request.data.get('apikey')

        if not apikey:
            return JsonResponse({'error': 'apikey is required'}, status=status.HTTP_403_FORBIDDEN)

        if apikey != instance.apikey:
            return Response({'error': 'Invalid apikey'}, status=status.HTTP_403_FORBIDDEN)
        if '/api/1.0/business_unit/suspend/' not in request.path or request.method != 'DELETE':
            if not instance.is_active:
                return JsonResponse({'error': 'Business unit is not active'}, status=status.HTTP_403_FORBIDDEN)

        return func(self, request, *args, **kwargs)

    return wrapper
