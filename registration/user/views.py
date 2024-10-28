import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers as django_serializers
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password

from registration import serializers
from registration.models import Delegate, PasswordReset, Registration, School, Workshop

import environ

env = environ.Env()
environ.Env.read_env()


@csrf_exempt
def users(request):
    """
    Handle requests related to all users

    GET - get all users
    """

    if request.method == "GET":
        user_data = django_serializers.serialize(
            "json", User.objects.filter(is_superuser=False)
        )

        return HttpResponse(user_data, content_type="application/json")
    else:
        return HttpResponse(status=405)


@csrf_exempt
def user(request):
    """
    Handle requests related to user

    GET - get logged in user
    PUT - update logged in user
    POST - create user
        {
            f_name: first name
            l_name: last name
            email: email (will act as username)
            password: password
            pronouns: pronouns
            year: year
            school_id: school
            workshop_1_id: id for session 1 workshop
            workshop_2_id: id for session 2 workshop
            workshop_3_id: id for session 3 workshop
        }
    DELETE - delete logged in user
    """

    user = request.user

    if request.method == "GET":
        if not user.is_authenticated:
            return HttpResponse("No user logged in", status=403)

        return HttpResponse(
            serializers.serialize_user(user), content_type="application/json"
        )
    elif request.method == "PUT":
        if not user.is_authenticated:
            return HttpResponse("No user logged in", status=403)

        data = json.loads(request.body)

        f_name = data.get("f_name")
        l_name = data.get("l_name")
        email = data.get("email")
        password = data.get("password")
        new_password = data.get("new_password")
        pronouns = data.get("pronouns")
        year = data.get("year")
        school_id = data.get("school_id")

        workshop_1_id = data.get("workshop_1_id")
        workshop_2_id = data.get("workshop_2_id")
        workshop_3_id = data.get("workshop_3_id")

        workshop_ids = [workshop_1_id, workshop_2_id, workshop_3_id]

        # update data

        if f_name and len(f_name) > 0:
            user.first_name = f_name

        if l_name and len(l_name) > 0:
            user.last_name = l_name

        if email and len(email) > 0:
            try:
                validate_email(email)
            except:
                return HttpResponse("Invalid email", status=400)

            if email != user.email and User.objects.filter(email=email).exists():
                return HttpResponse("Email already in use", status=400)

            user.email = email

        if new_password and len(new_password) > 0:
            if not authenticate(username=user.username, password=password):
                return JsonResponse(
                    {"message": "Old password does not match"}, status=409
                )

            if validate_password(new_password) < 0:
                return HttpResponse("Password is not strong enough", status=400)
            user.set_password(password)

        if pronouns and len(pronouns) > 0:
            user.delegate.pronouns = pronouns

        if year and len(year) > 0:
            user.delegate.year = year

        if school_id:
            user.delegate.school_id = school_id

        # workshops
        sessions = []
        for workshop_id in workshop_ids:
            if workshop_id:
                session = Workshop.objects.get(pk=workshop_id).session

                if session in sessions:
                    return HttpResponse(
                        "Can not register for multiple workshops in a single session"
                    )

                sessions.append(session)

        print(sessions)
        print(workshop_ids)

        if len(sessions) == 3:
            # clear registered workshops
            Registration.objects.filter(user=user).delete()

            # re register
            for workshop_id in workshop_ids:
                workshop = Workshop.objects.get(pk=workshop_id)

                registration = Registration(user=user, workshop=workshop)

                registration.save()

        user.save()
        user.delegate.save()

        return HttpResponse(
            serializers.serialize_user(user), content_type="application/json"
        )
    elif request.method == "POST":
        data = json.loads(request.body)

        f_name = data.get("f_name")
        l_name = data.get("l_name")
        email = data.get("email")
        password = data.get("password")
        pronouns = data.get("pronouns")
        year = data.get("year")
        school_id = data.get("school_id")
        workshop_1_id = data.get("workshop_1_id")
        workshop_2_id = data.get("workshop_2_id")
        workshop_3_id = data.get("workshop_3_id")

        workshop_ids = [workshop_1_id, workshop_2_id, workshop_3_id]

        # validate data
        if not f_name or len(f_name) < 1:
            return JsonResponse(
                {"message": "First name must be at least one character"}, status=400
            )

        if not l_name or len(l_name) < 1:
            return JsonResponse(
                {"message": "Last name must be at least one character"}, status=400
            )

        try:
            validate_email(email)
        except:
            return JsonResponse({"message": "Invalid email"}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"message": "Email already in use"}, status=400)

        if not password or len(password) < 8:
            return JsonResponse(
                {"message": "Password must be at least 8 characters"}, status=400
            )

        sessions = []
        for workshop_id in workshop_ids:
            session = Workshop.objects.get(pk=workshop_id).session

            if session in sessions:
                return JsonResponse(
                    {
                        "message": "Can not register for multiple workshops in a single session"
                    },
                    status=400,
                )

            sessions.append(session)

        # set user data
        user = User(username=email, email=email, first_name=f_name, last_name=l_name)
        user.set_password(password)

        user.save()

        # set delegate data
        school = None

        if school_id:
            try:
                school = School.objects.get(pk=school_id)
            except:
                school = None

        delegate = Delegate(user=user, pronouns=pronouns, year=year, school=school)
        delegate.save()

        workshop_details = {}

        # set registration data
        for workshop_id in workshop_ids:
            workshop = Workshop.objects.get(pk=workshop_id)

            registration = Registration(user=user, workshop=workshop)
            registration.save()

            # save workshop names for email
            workshop_details[workshop.session] = workshop.title

        # login
        login(request, user)

        # send email
        subject = f"FACT 2024 Registration Confirmation - {f_name} {l_name}"

        registration_details = ""
        for session in workshop_details:
            registration_details += f"Session {session}: {workshop_details[session]}\n"

        body = f"Thank you for registering for FACT 2024!\n\nYou have registered for the following workshops\n\n{registration_details}\nTo update your personal information, change workshops, and view up to date conference information, visit fact.psauiuc.org/my-fact/dashboard"
        from_email = env("EMAIL_HOST_USER")
        to_email = [email]

        send_mail(subject, body, from_email, to_email)

        return HttpResponse(
            serializers.serialize_user(user), content_type="application/json"
        )
    elif request.method == "DELETE":
        if not user.is_authenticated:
            return JsonResponse({"message": "No user logged in"}, status=403)

        data = serializers.serialize_user(user)

        user.delete()
        user.save()

        return HttpResponse(data, content_type="application/json")
    else:
        return JsonResponse({"message": "Method not allowed"}, status=405)


@csrf_exempt
def login_user(request):
    user = request.user

    if request.method == "POST":
        data = json.loads(request.body)

        username = data.get("username")
        password = data.get("password")

        if username is None or len(username) == 0:
            return JsonResponse({"message": "Must provide email"}, status=400)

        if password is None or len(password) == 0:
            return JsonResponse({"message": "Must provide password"}, status=400)

        user = authenticate(username=username, password=password)

        if user is None:
            return JsonResponse({"message": "Invalid credentials"}, status=400)

        login(request, user)
        
        return HttpResponse(
            serializers.serialize_facilitator(user), content_type="application/json"
        )
    else:
        return JsonResponse({"message": "Method not allowed"}, status=405)


@csrf_exempt
def logout_user(request):
    user = request.user
    if request.method == "POST":
        if not user.is_authenticated:
            return JsonResponse({"message": "No user logged in"}, status=403)

        logout(request)

        return JsonResponse({"message": "Logout successful"})
    else:
        return JsonResponse({"message": "Method not allowed"}, status=405)


@csrf_exempt
def request_password_reset(request):
    if request.method == "POST":
        data = json.loads(request.body)

        email = data.get("email")

        if not email or email == "":
            return JsonResponse({"message": "Must provide email"}, status=400)

        try:
            user = User.objects.get(email=email)
        except:
            return JsonResponse(
                {
                    "message": "If email is connected to account, reset password link has been sent"
                }
            )

        user = User.objects.get(email=email)

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)

        reset = PasswordReset(
            email=email,
            token=token,
            expiration=timezone.now() + timezone.timedelta(minutes=15),
        )
        reset.save()

        reset_url = f"{env('RESET_PASSWORD_URL')}/{token}"

        # send email
        subject = "FACT Account Password Reset"
        body = f"Hi {user.first_name}. You are receiving this email because you requested a password reset. Click on the link to create a new password\n\n{reset_url}\n\n If you didn't request a password reset, you can ignore this email. Your password will not be changed. This link will expire in 15 minutes."
        from_email = env("EMAIL_HOST_USER")
        to_email = [email]

        send_mail(subject, body, from_email, to_email)

        # always send "success" message even if user doesn't exist
        return JsonResponse(
            {
                "message": "If email is connected to account, reset password link has been sent"
            }
        )
    else:
        return JsonResponse({"message": "Method not allowed"}, status=405)


@csrf_exempt
def reset_password(request):
    if request.method == "POST":
        data = json.loads(request.body)

        password = data.get("password")
        token = data.get("token")

        if not password or password == "":
            return JsonResponse({"message": "Must provide password"}, status=400)

        if not token or token == "":
            return JsonResponse({"message": "Must provide token"}, status=400)

        PasswordReset.objects.filter(expiration__lt=timezone.now()).delete()

        try:
            reset = PasswordReset.objects.get(token=token)
            email = reset.email
            reset.delete()

            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
        except:
            return JsonResponse({"message": "Invalid reset token"}, status=409)

        return JsonResponse({"message": "success"})
    else:
        return JsonResponse({"message": "Method not allowed"}, status=405)
