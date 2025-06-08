from django.contrib import admin
# Make sure all your models are imported here, including Document
from .models import CrewMember, CommunicationLog, NextOfKin, ProfessionalReference, Appraisal, Principal, Vessel, Document, ExperienceHistory
from django.contrib.auth.models import User # <--- ADD THIS LINE

# Register your models here.
admin.site.register(CrewMember)
admin.site.register(CommunicationLog)
admin.site.register(NextOfKin)
admin.site.register(ProfessionalReference)
admin.site.register(Appraisal)
admin.site.register(Principal)
admin.site.register(Vessel)
admin.site.register(Document) # <--- This line must be present and correctly spelled
admin.site.register(ExperienceHistory)