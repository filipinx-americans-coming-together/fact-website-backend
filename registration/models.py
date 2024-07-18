from django.db import models

# Create your models here.

class Workshop(models.Model):
    workshop_title = models.CharField(max_length=100)

class Location(models.Model):
    room_num = models.CharField(max_length=50, default="")
    building = models.CharField(max_length=50, default="")
    capacity = models.IntegerField(default=0)