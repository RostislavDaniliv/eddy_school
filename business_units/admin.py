from django.contrib import admin

from business_units.forms import BusinessGoogleCredsForm
from business_units.models import BusinessUnit


@admin.register(BusinessUnit)
class BusinessUnitAdmin(admin.ModelAdmin):
    form = BusinessGoogleCredsForm
    list_display = (
        "id",
        "apikey",
        "name",
        "gpt_api_key",
    )
    readonly_fields = ('apikey', 'sendpulse_token', 'last_update_sendpulse', )
