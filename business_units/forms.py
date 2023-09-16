from django import forms
from .models import BusinessUnit


class BusinessGoogleCredsForm(forms.ModelForm):
    class Meta:
        model = BusinessUnit
        fields = '__all__'
