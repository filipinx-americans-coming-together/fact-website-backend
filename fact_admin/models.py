from django.db import models

from registration.models import Location


class Notification(models.Model):
    message = models.CharField(max_length=180)
    expiration = models.DateTimeField()

class Session(models.Model):
    session_num = models.IntegerField()
    session_name = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

class AgendaItem(models.Model):
    title = models.CharField(max_length=200)
    session = models.ForeignKey(Session, null=True, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, null=True, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
