from django.contrib import admin
from .models import (
    AccountSetUp,
    FacilitatorAssistant,
    FacilitatorRegistration,
    FacilitatorWorkshop,
    NewSchool,
    Workshop,
    Location,
    Facilitator,
    School,
    Delegate,
    Registration,
)

admin.site.register(Workshop)
admin.site.register(Location)
admin.site.register(Facilitator)
admin.site.register(School)
admin.site.register(Delegate)
admin.site.register(Registration)
admin.site.register(FacilitatorRegistration)
admin.site.register(FacilitatorWorkshop)
admin.site.register(FacilitatorAssistant)
admin.site.register(NewSchool)
