import json
from django.http import FileResponse, HttpResponse, JsonResponse
from django.core import serializers as django_serializers
from django.contrib.auth.models import User
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import os

import pandas as pd

from fact_admin.models import RegistrationFlag
from registration.models import Delegate, Location, Registration, School, Workshop, Facilitator, AccountSetUp

# set workshop locations
# get summary (sheet)
# get locations (sheet)
# reset database
# send email updates?


def registration_flags(request):
    """
    GET: List all registration flags
    """
    if request.method == "GET":
        data = django_serializers.serialize("json", RegistrationFlag.objects.all())
        return HttpResponse(data, content_type="application/json")
    else:
        return JsonResponse({"message": "method not allowed"}, status=405)


def registration_flag_id(request, label):
    """
    GET: Get flag by label
    PUT: Update flag value (admin only)
    """
    if request.method == "GET":
        flag = RegistrationFlag.objects.filter(label=label)

        if not flag.exists():
            return JsonResponse({"message": "Permission not found"}, status=404)

        return HttpResponse(
            django_serializers.serialize("json", flag),
            content_type="application/json",
        )
    if request.method == "PUT":
        # must be admin
        if not request.user.groups.filter(name="FACTAdmin").exists():
            return JsonResponse(
                {"message": "Must be admin to make this request"}, status=403
            )

        flag = RegistrationFlag.objects.filter(label=label)

        if not flag.exists():
            return JsonResponse({"message": "Flag not found"}, status=404)

        data = json.loads(request.body)
        value = data.get("value")

        if value == None or (value != True and value != False):
            return JsonResponse(
                {"message": "Must provide true/false value"}, status=400
            )

        flag_obj = flag.first()
        flag_obj.value = value
        flag_obj.save()

        return HttpResponse(django_serializers.serialize("json", flag))
    else:
        return JsonResponse({"message": "method not allowed"}, status=405)


def summary(request):
    """
    GET: Event stats (admin only)
    Returns: delegate count, school count, recent registrations (past 5 days)
    """
    if not request.user.groups.filter(name="FACTAdmin").exists():
        return JsonResponse(
            {"message": "Must be admin to make this request"}, status=403
        )

    if request.method == "GET":
        # delegates = Delegate.objects.all().count()
        delegates = Registration.objects.values("delegate").distinct().count()
        schools = (
            Delegate.objects.values("school")
            .distinct()
            .count()
            # + Delegate.objects.values("other_school").distinct().count()
        )

        registrations = Delegate.objects.filter(
            date_created__gt=timezone.now() - timezone.timedelta(days=5)
        ).values_list("date_created", flat=True)

        return JsonResponse(
            {
                "delegates": delegates,
                "schools": schools,
                "registrations": list(registrations),
            },
            safe=False,
        )
    else:
        return JsonResponse({"message": "method not allowed"}, status=405)


def delegate_sheet(request):
    """
    GET: Export delegate info to Excel (admin only)
    Includes: personal info, school, workshop selections
    """
    if not request.user.groups.filter(name="FACTAdmin").exists():
        return JsonResponse(
            {"message": "Must be admin to make this request"}, status=403
        )

    if request.method == "GET":
        delegates = Delegate.objects.all().values()
        df = pd.DataFrame.from_records(delegates)

        for idx, row in df.iterrows():
            # Handle missing user_id
            if not pd.isna(row["user_id"]):
                try:
                    user = User.objects.get(pk=row["user_id"])
                    df.at[idx, "first_name"] = user.first_name
                    df.at[idx, "last_name"] = user.last_name
                    df.at[idx, "email"] = user.email
                except User.DoesNotExist:
                    print(f"User with ID {row['user_id']} does not exist.")
                    df.at[idx, "first_name"] = None
                    df.at[idx, "last_name"] = None
                    df.at[idx, "email"] = None
            else:
                df.at[idx, "first_name"] = None
                df.at[idx, "last_name"] = None
                df.at[idx, "email"] = None

            # Handle missing school_id or other_school
            if not pd.isna(row["school_id"]):
                try:
                    df.at[idx, "school"] = School.objects.get(pk=row["school_id"]).name
                except School.DoesNotExist:
                    df.at[idx, "school"] = None
            elif row.get("other_school"):
                df.at[idx, "school"] = row["other_school"]
            else:
                df.at[idx, "school"] = None

            # Handle workshop registrations
            registrations = Registration.objects.filter(delegate_id=row["id"])
            for registration in registrations.values():
                if not pd.isna(registration["workshop_id"]):
                    try:
                        workshop = Workshop.objects.get(pk=registration["workshop_id"])
                        for i in range(1, 4):
                            if workshop.session == i:
                                df.at[idx, f"session_{i}"] = workshop.title
                    except Workshop.DoesNotExist:
                        print(f"Workshop with ID {registration['workshop_id']} does not exist.")
                else:
                    print(f"Skipping registration with NaN workshop_id for delegate {row['id']}.")

        # Drop unwanted columns
        df.drop(
            ["id", "user_id", "other_school", "school_id", "date_created"],
            axis=1,
            inplace=True,
        )

        # Save the Excel file
        file_path = "delegates.xlsx"
        df.to_excel(file_path, index=False)

        # Return the file as a response
        response = FileResponse(open(file_path, "rb"))
        response["Content-Disposition"] = f'attachment; filename="{file_path}"'
        return response

    else:
        return JsonResponse({"message": "method not allowed"}, status=405)


def location_sheet(request):
    """
    GET: Export workshop locations to Excel (admin only)
    Includes: workshop details, location, capacity info
    """
    if not request.user.groups.filter(name="FACTAdmin").exists():
        return JsonResponse(
            {"message": "Must be admin to make this request"}, status=403
        )

    if request.method == "GET":
        # Fetch workshops with required fields
        workshops = Workshop.objects.all().values(
            "id", "title", "session", "location_id", "preferred_cap", "moveable_seats"
        )
        df = pd.DataFrame.from_records(workshops)

        # Convert fields to string for Excel compatibility
        df["preferred_cap"] = df["preferred_cap"].astype(str)
        df["moveable_seats"] = df["moveable_seats"].astype(str)

        for idx, row in df.iterrows():
            # Handle location_id and resolve location details
            location_id = row.get("location_id")
            if location_id is not None:
                try:
                    location = Location.objects.get(pk=location_id)
                    df.at[idx, "location"] = f"{location.building} {location.room_num}"
                except Location.DoesNotExist:
                    print(f"Location with ID {location_id} does not exist.")
                    df.at[idx, "location"] = "Unknown Location"
            else:
                print(f"Missing location_id for workshop at index {idx}.")
                df.at[idx, "location"] = "No Location Assigned"

            # Handle preferred_cap
            preferred_cap = row.get("preferred_cap")
            if preferred_cap is not None and not pd.isna(preferred_cap):
                df.at[idx, "preferred_cap"] = str(preferred_cap)
            else:
                df.at[idx, "preferred_cap"] = "No Preference"

            # Handle moveable_seats
            moveable_seats = row.get("moveable_seats")
            if moveable_seats is not None:
                df.at[idx, "moveable_seats"] = "Yes" if moveable_seats else "No"
            else:
                df.at[idx, "moveable_seats"] = "Unknown"

        # Drop unwanted columns
        df.drop(["id", "location_id"], axis=1, inplace=True, errors="ignore")

        # Save the Excel file
        file_path = "locations.xlsx"
        df.to_excel(file_path, index=False)

        # Return the file as a response
        response = FileResponse(open(file_path, "rb"))
        response["Content-Disposition"] = f'attachment; filename="{file_path}"'
        return response
    else:
        return JsonResponse({"message": "method not allowed"}, status=405)


# TODO: change to send individual emails to facilitators
# TODO: change recipients to facilitator emails
@csrf_exempt
def send_facilitator_links(request):
    """
    POST: Send login links to all existing facilitators (admin only)
    Uses existing AccountSetUp records to send facilitators their login links
    Returns 403 for non-admin, 200 on success
    """
    # if not request.user.groups.filter(name="FACTAdmin").exists():
    #     return JsonResponse(
    #         {"message": "Must be admin to make this request"}, status=403
    #     )

    if request.method == "POST":
        facilitators = Facilitator.objects.all()

        if facilitators.count() == 0:
            return JsonResponse(
                {"message": "No facilitators found"}, status=404
            )

        # Collect facilitator info with their account setup tokens
        facilitator_links = []
        for facilitator in facilitators:
            account_setup = AccountSetUp.objects.filter(username=facilitator.user.username).first()
            
            if account_setup:
                # Login link using the stored token
                login_url = f"{os.getenv('ACCOUNT_SET_UP_URL')}/{account_setup.token}"
                
                facilitator_links.append(
                    (facilitator.department_name, facilitator.user.username, login_url)
                )

        if not facilitator_links:
            return JsonResponse(
                {"message": "No account setups found for facilitators"}, status=404
            )

        # Send email with all facilitator links
        subject = "FACT Facilitator Login Links"
        body = "Facilitator login links:\n\n"

        for facilitator in facilitator_links: # TODO: change to send individual emails
            body += f"Facilitator: {facilitator[0]}\nUsername: {facilitator[1]}\nLogin Link: {facilitator[2]}\n\n"

        from_email = os.getenv("EMAIL_HOST_USER")
        to_email = ["fact.it@psauiuc.org"] # TODO: change to facilitator email

        send_mail(subject, body, from_email, to_email)

        return JsonResponse(
            {"message": f"Successfully sent login links for {len(facilitator_links)} facilitators"},
            status=200
        )
    else:
        return JsonResponse({"message": "method not allowed"}, status=405)