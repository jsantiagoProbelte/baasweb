from django.contrib import admin
# Register your models here.
from trialapp.models import FieldTrial, Crop, Phase, Project, Objective,\
    RateUnit, Product, Plague, TrialStatus, AssessmentUnit, AssessmentType


class FieldTrialAdmin(admin.ModelAdmin):
    # list_filter = ["location","chain"]
    search_fields = ["name"]


admin.site.register(FieldTrial, FieldTrialAdmin)
admin.site.register(Crop)
admin.site.register(Phase)
admin.site.register(Project)
admin.site.register(Objective)
admin.site.register(RateUnit)
admin.site.register(Product)
admin.site.register(Plague)
admin.site.register(TrialStatus)
admin.site.register(AssessmentUnit)
admin.site.register(AssessmentType)
