from django.contrib import admin
# Register your models here.
from trialapp.models import FieldTrial, Crop, TrialType, Project, Objective,\
    RateUnit, Plague, TrialStatus, AssessmentUnit, AssessmentType, ProductThesis


class FieldTrialAdmin(admin.ModelAdmin):
    # list_filter = ["location","chain"]
    search_fields = ["name", "crop", "product"]


admin.site.register(FieldTrial, FieldTrialAdmin)
admin.site.register(Crop)
admin.site.register(TrialType)
admin.site.register(TrialStatus)
admin.site.register(Project)
admin.site.register(Objective)
admin.site.register(RateUnit)
admin.site.register(Plague)
admin.site.register(AssessmentUnit)
admin.site.register(AssessmentType)
admin.site.register(ProductThesis)
