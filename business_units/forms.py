from django import forms
from .models import BusinessUnit, Document


class BusinessGoogleCredsForm(forms.ModelForm):
    class Meta:
        model = BusinessUnit
        fields = '__all__'


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = '__all__'
