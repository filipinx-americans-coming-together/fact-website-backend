from django.db import models


class Notification(models.Model):
    message = models.CharField(max_length=180)
    expiration = models.DateTimeField()