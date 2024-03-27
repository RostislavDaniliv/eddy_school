from django.contrib import admin
from import_export.admin import ExportMixin
from rangefilter.filters import DateRangeFilterBuilder

from chat_history.forms import ChatHistoryForm
from chat_history.models import ChatHistory
from chat_history.resources import ChatHistoryResource


@admin.register(ChatHistory)
class ChatHistoryAdmin(ExportMixin, admin.ModelAdmin):
    form = ChatHistoryForm
    resource_class = ChatHistoryResource
    list_display = (
        "id",
        "business_unit",
        "username",
        "user_id",
        "user_question",
        "created_at"
    )
    list_filter = (
        ("created_at", DateRangeFilterBuilder()),
        "business_unit",
    )
