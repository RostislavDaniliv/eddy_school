from django import forms

from chat_history.models import ChatHistory


class ChatHistoryForm(forms.ModelForm):
    class Meta:
        model = ChatHistory
        fields = '__all__'
