from rest_framework import serializers

from business_units.models import BusinessUnit


class BusinessUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessUnit
        fields = '__all__'
