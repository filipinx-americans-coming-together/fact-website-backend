from django.db import models

from registration.models import Location


class Notification(models.Model):
    """
    System notifications with expiration dates.
    Used for displaying time-sensitive messages to admins.
    """
    message = models.CharField(
        max_length=180,
        help_text="The notification message to be displayed (max 180 characters)"
    )
    expiration = models.DateTimeField(
        help_text="The date and time when this notification should expire"
    )


class AgendaItem(models.Model):
    """
    Event schedule items.
    Tracks location, timing, and session info for each event.
    """
    title = models.CharField(
        max_length=200,
        help_text="The title or name of the agenda item"
    )
    building = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        help_text="Optional building where the event will take place"
    )
    room_num = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        help_text="Optional room number where the event will take place"
    )
    start_time = models.DateTimeField(
        help_text="The scheduled start time of the event"
    )
    end_time = models.DateTimeField(
        help_text="The scheduled end time of the event"
    )
    session_num = models.IntegerField(
        null=True,
        blank=True,
        help_text="Optional session number for events with multiple sessions"
    )
    address = models.CharField(
        null=True,
        blank=True,
        max_length=200,
        help_text="Optional address for events"
    )


class RegistrationFlag(models.Model):
    """
    Feature flags for registration system.
    Controls access to registration features and functionality.
    """
    label = models.CharField(
        max_length=200,
        help_text="Unique identifier for the flag"
    )
    value = models.BooleanField(
        help_text="The current state of the flag (True/False)"
    )

    def __str__(self):
        return f"{self.label} - {self.value}"
