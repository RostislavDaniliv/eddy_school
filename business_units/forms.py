from django import forms

from .models import BusinessUnit, Document, SimpleQuestions


class BusinessGoogleCredsForm(forms.ModelForm):
    class Meta:
        model = BusinessUnit
        fields = '__all__'
        widgets = {
            'is_trial_user_limits': forms.CheckboxInput(attrs={'onchange': 'toggleTrialLimitFields();'}),
        }


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = '__all__'


class SimpleQuestionsForm(forms.ModelForm):
    class Meta:
        model = SimpleQuestions
        fields = '__all__'


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()
