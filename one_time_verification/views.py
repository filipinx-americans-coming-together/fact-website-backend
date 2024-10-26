import json
import environ
import secrets

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.utils import timezone
from django.core.validators import validate_email

from one_time_verification.models import PendingVerification

env = environ.Env()
environ.Env.read_env()


@csrf_exempt
def request_verification(request):
    """
    Handle requests for verifications
    """

    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        email_subject = data.get("email_subject")

        if not email or email == "":
            return JsonResponse({"message": "Must include email"}, status=400)

        try:
            validate_email(email)
        except:
            return JsonResponse({"message": "Invalid email"}, status=400)
        
        if not email_subject or email_subject == "":
            return JsonResponse({"message": "Must include email_subject"}, status=400)

        # remove existing codes
        PendingVerification.objects.filter(email=email).delete()

        # create code
        expire_time = 15

        code = ""
        choices = [0] * 10

        for i in range(10):
            choices[i] = i

        for i in range(6):
            code += str(secrets.choice(choices))

        PendingVerification.objects.create(
            email=email,
            code=code,
            expiration=timezone.now() + timezone.timedelta(minutes=expire_time),
        )

        # send email
        subject = email_subject

        body = f"{email_subject}\nYour one-time verification code is {code}. It will expire in {expire_time} minutes. Do not share this code."
        from_email = env("EMAIL_HOST_USER")
        to_email = [email]

        send_mail(subject, body, from_email, to_email)

        return JsonResponse({"message": "Created verification code"})
    else:
        return JsonResponse({"message": "Method not allowed"}, status=405)


@csrf_exempt
def verify(request):
    """
    Handle attempts to verify
    """

    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        code = data.get("code")

        if not email or email == "":
            return JsonResponse({"message": "Must provide email"}, status=400)

        if not code or code == "":
            return JsonResponse({"message": "Must provide code"}, status=400)

        # remove expired codes
        PendingVerification.objects.filter(expiration__lt=timezone.now()).delete()

        if not PendingVerification.objects.filter(email=email, code=code).exists():
            return JsonResponse({"message": "Email and code do not match"}, status=409)
        
        # remove
        PendingVerification.objects.filter(email=email, code=code).delete()

        return JsonResponse({"message": "Email verified"})
    else:
        return JsonResponse({"message": "Method not allowed"}, status=405)
