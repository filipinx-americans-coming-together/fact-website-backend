from django.contrib import admin

from fact_admin.models import AgendaItem, Notification, RegistrationFlag

# Register your models here.
admin.site.register(AgendaItem)
admin.site.register(Notification)
admin.site.register(RegistrationFlag)
