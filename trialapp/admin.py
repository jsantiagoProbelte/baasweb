from django.contrib import admin

# Register your models here.
from trialapp.models import FieldTrial


class FieldTrialAdmin(admin.ModelAdmin):
    # list_filter = ["location","chain"]
    search_fields = ["name"]


admin.site.register(FieldTrial, FieldTrialAdmin)
