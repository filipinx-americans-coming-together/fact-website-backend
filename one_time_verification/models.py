from django.db import models

class PendingVerification(models.Model):
    email=models.TextField()
    code=models.CharField(max_length=6)
    expiration=models.DateTimeField()