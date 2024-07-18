from django.db import models
# from django.contrib.auth.hashers import make_password

# Create your models here.

class Location(models.Model):
    room_num = models.CharField(max_length=50, default="")
    building = models.CharField(max_length=50, default="")
    capacity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.room_num} - {self.building}"

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
        return f"{self.title} - {self.session}"

# class Delegate(models.Model):
#     username = models.CharField(max_length=50)
#     password = models.CharField(max_length=30)
#     email = models.EmailField()
#     workshops = models.ManyToManyField(Workshop, related_name='delegates')

#     def save(self, *args, **kwargs):
#         self.password = make_password(self.password)
#         super(Delegate, self).save(*args, **kwargs)