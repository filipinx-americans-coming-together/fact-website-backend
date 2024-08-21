from django.db import models
from django.contrib.auth.models import User

class Location(models.Model):
    room_num = models.CharField(max_length=50, default="")
    building = models.CharField(max_length=50, default="")
    capacity = models.IntegerField(default=0)
    session = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.room_num} - {self.building}, session {self.session}"

class Workshop(models.Model):
    title = models.CharField(max_length=100, default="")
    description = models.TextField()
    facilitators = models.JSONField(default=list)
    location = models.OneToOneField(
        Location,
        on_delete=models.CASCADE,
        primary_key=True,
        )
    session = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} - session {self.session}"
    
class School(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.name}'

class Delegate(models.Model):
    # django user model - https://docs.djangoproject.com/en/5.0/topics/auth/default/#user-objects
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pronouns = models.CharField(max_length=30, default="")
    year = models.CharField(max_length=40)
    school = models.ForeignKey(School, default=None, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.last_name}, {self.user.first_name} - {self.user.email}'

class Registration(models.Model):
    delegate = models.ForeignKey(Delegate, on_delete=models.CASCADE)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE)

