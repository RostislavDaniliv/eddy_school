from datetime import datetime

from django.db import models

from business_units.models import BusinessUnit


class ChatHistory(models.Model):
    business_unit = models.ForeignKey(
        BusinessUnit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Business Unit'
    )
    username = models.CharField(max_length=200, blank=True, null=True, verbose_name='User name')
    user_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="User ID")
    user_question = models.TextField(blank=True, null=True, verbose_name="User Question")
    system_answer = models.TextField(blank=True, null=True, verbose_name="System Answer")
    created_at = models.DateTimeField(auto_now_add=datetime.now())

    def __str__(self):
        return f"{self.business_unit} - {self.username} - {self.created_at}"
