from django.db import models

# Create your models here.

class Workshop(models.Model):
    workshop_title = models.CharField(max_length=100)