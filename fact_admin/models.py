from django.db import models

from registration.models import Location


class Notification(models.Model):
    message = models.CharField(max_length=180)
    expiration = models.DateTimeField()

class AgendaItem(models.Model):
    title = models.CharField(max_length=200)
    building = models.CharField(max_length=100)
    room_num = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    session_num = models.IntegerField(null=True, blank=True)