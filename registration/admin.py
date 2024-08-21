from django.contrib import admin
from .models import Workshop, Location, School, Delegate, Registration

admin.site.register(Workshop)
admin.site.register(Location)
admin.site.register(School)
admin.site.register(Delegate)
admin.site.register(Registration)

