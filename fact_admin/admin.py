from django.contrib import admin

from fact_admin.models import AgendaItem, Notification, RegistrationPermission

# Register your models here.
admin.site.register(AgendaItem)
admin.site.register(Notification)
admin.site.register(RegistrationPermission)