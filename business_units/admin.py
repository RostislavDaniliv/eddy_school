from django.contrib import admin

from business_units.forms import BusinessGoogleCredsForm, DocumentForm
from business_units.models import BusinessUnit, Document, SimpleQuestions


class SimpleQuestionsInline(admin.TabularInline):
    model = SimpleQuestions
    extra = 1


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    form = DocumentForm
    list_display = (
        "id",
        "name",
        "document_id",
        "business_unit",
    )


@admin.register(BusinessUnit)
class BusinessUnitAdmin(admin.ModelAdmin):
    inlines = [SimpleQuestionsInline]
    form = BusinessGoogleCredsForm
    list_display = (
        "id",
        "apikey",
        "name",
        "gpt_api_key",
        "is_active",
    )
    readonly_fields = (
        'apikey', 'sendpulse_token', 'last_update_sendpulse', 'last_update_document', 'last_used_documents_list'
    )
