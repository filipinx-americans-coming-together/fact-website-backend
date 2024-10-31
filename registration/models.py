from django.db import models
from django.contrib.auth.models import User


class Location(models.Model):
    room_num = models.CharField(max_length=50, default="")
    building = models.CharField(max_length=50, default="")
    capacity = models.IntegerField(default=0)
    session = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.room_num} - {self.building}, session {self.session}"


class Facilitator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fa_name = models.CharField(max_length=100, blank=True)
    fa_contact = models.CharField(max_length=100, blank=True)
    department_name = models.CharField(max_length=100)
    facilitators = models.JSONField(default=list)
    image_url = models.URLField()
    bio = models.TextField()

    def __str__(self):
        return f"{self.department_name} - {self.fa_name}"


class Workshop(models.Model):
    title = models.CharField(max_length=100, default="")
    description = models.TextField()
    location = models.OneToOneField(
        Location, on_delete=models.CASCADE, null=True, blank=True
    )
    session = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} - session {self.session}"


class School(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"


class NewSchool(models.Model):
    name = models.CharField(max_length=100)


class Delegate(models.Model):
    # django user model - https://docs.djangoproject.com/en/5.0/topics/auth/default/#user-objects
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pronouns = models.CharField(max_length=30, default="")
    year = models.CharField(max_length=40, null=True, default="")
    school = models.ForeignKey(
        School, default=None, null=True, on_delete=models.CASCADE
    )
    other_school = models.CharField(max_length=100, null=True, blank=True)

    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.last_name}, {self.user.first_name} - {self.user.email}"


class Registration(models.Model):
    delegate = models.ForeignKey(Delegate, on_delete=models.CASCADE)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE)


class FacilitatorRegistration(models.Model):
    facilitator_name = models.CharField(max_length=200)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE)


class FacilitatorWorkshop(models.Model):
    facilitator = models.ForeignKey(Facilitator, on_delete=models.CASCADE)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.facilitator} - {self.workshop}"


class FacilitatorAssistant(models.Model):
    name = models.CharField(max_length=200)
    contact = models.CharField(max_length=100)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE)


class PasswordReset(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=100)
    expiration = models.DateTimeField()


class AccountSetUp(models.Model):
    username = models.CharField(max_length=30)
    token = models.CharField(max_length=100)
    expiration = models.DateTimeField()
