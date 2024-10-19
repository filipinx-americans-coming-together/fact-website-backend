from django.db import models

class Ticket(models.Model):
    first_name=models.CharField(max_length=70)
    last_name=models.CharField(max_length=70)
    email=models.CharField(max_length=200)
    