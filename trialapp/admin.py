from django.contrib import admin
# Register your models here.
from trialapp.models import FieldTrial, Crop, TrialType, Project, Objective,\
    Plague, TrialStatus, Irrigation, CropVariety, ApplicationMode,\
    CultivationMethod, TreatmentThesis
from trialapp.data_models import Assessment
from baaswebapp.models import Weather


class FieldTrialAdmin(admin.ModelAdmin):
    search_fields = ["name", "crop", "product"]


admin.site.register(FieldTrial, FieldTrialAdmin)
admin.site.register(Crop)
admin.site.register(TrialType)
admin.site.register(TrialStatus)
admin.site.register(Project)
admin.site.register(Objective)
admin.site.register(Plague)
admin.site.register(Assessment)
admin.site.register(CropVariety)
admin.site.register(Irrigation)
admin.site.register(ApplicationMode)
admin.site.register(CultivationMethod)
admin.site.register(TreatmentThesis)
admin.site.register(Weather)
