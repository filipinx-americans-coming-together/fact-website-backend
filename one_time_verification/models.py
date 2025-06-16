from django.db import models

class PendingVerification(models.Model):
    """
    One-time verification codes for email verification.
    Codes expire after 15 minutes.
    """
    email = models.TextField()
    code = models.CharField(max_length=6)
    expiration = models.DateTimeField()