import csv

from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.utils.html import format_html

from business_units.forms import BusinessGoogleCredsForm, DocumentForm, CsvImportForm, SimpleQuestionsForm
from business_units.models import BusinessUnit, Document, SimpleQuestions, TestUser


@admin.register(SimpleQuestions)
class DocumentAdmin(admin.ModelAdmin):
    form = SimpleQuestionsForm
    list_display = (
        "id",
        "business_unit",
        "question",
        "answer",
    )


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


class BusinessUnitAdmin(admin.ModelAdmin):
    inlines = [SimpleQuestionsInline]
    form = BusinessGoogleCredsForm
    list_display = (
        "id",
        "apikey",
        "name",
        "gpt_api_key",
        "is_active",
        'import_questions_button',
    )
    readonly_fields = (
        'apikey', 'sendpulse_token', 'last_update_sendpulse', 'last_update_document', 'last_used_documents_list'
    )

    def import_questions_button(self, obj):
        return format_html('<a class="button" href="{}">Import Questions</a>',
                           reverse('admin:import-questions', args=[obj.pk]))

    import_questions_button.short_description = 'Import Questions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/import-questions/',
                self.admin_site.admin_view(self.import_questions),
                name='import-questions',
            ),
        ]
        return custom_urls + urls

    def import_questions(self, request, object_id):
        business_unit = self.get_object(request, object_id)

        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            decoded_file = csv_file.read().decode('utf-8')
            reader = csv.reader(decoded_file.splitlines())
            next(reader, None)
            SimpleQuestions.objects.filter(business_unit=business_unit).delete()
            for row in reader:
                question, answer = row
                SimpleQuestions.objects.create(business_unit=business_unit, question=question, answer=answer)
            self.message_user(request, "Questions imported successfully")
            return redirect("..")

        form = CsvImportForm()
        payload = {"form": form, "title": "Import questions"}
        return render(request, "admin/csv_form.html", payload)


admin.site.register(TestUser)


admin.site.register(BusinessUnit, BusinessUnitAdmin)
