import json
from django.http import FileResponse, HttpResponse, JsonResponse
from django.core import serializers as django_serializers
from django.contrib.auth.models import User
from django.utils import timezone

import pandas as pd

from fact_admin.models import RegistrationFlag
from registration.models import Delegate, Location, Registration, School, Workshop

# set workshop locations
# get summary (sheet)
# get locations (sheet)
# reset database
# send email updates?


def registration_flags(request):
    if request.method == "GET":
        data = django_serializers.serialize("json", RegistrationFlag.objects.all())
        return HttpResponse(data, content_type="application/json")
    else:
        return JsonResponse({"message": "method not allowed"}, status=405)


def registration_flag_id(request, label):
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
    Get event summary
    - number of delegates
    - number of unique schools
    - registrations from past 5 days
    """
    if not request.user.groups.filter(name="FACTAdmin").exists():
        return JsonResponse(
            {"message": "Must be admin to make this request"}, status=403
        )

    if request.method == "GET":
        delegates = Delegate.objects.all().count()
        schools = (
            Delegate.objects.values("school")
            .distinct()
            .count()
            # + Delegate.objects.values("other_school").distinct().count()
        )

        # this might only work for this year, since it uses delegates as the base
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
    Spreadsheet of delegate info, does not include individual facilitators
    - first_name
    - last_name
    - email
    - pronouns
    - year
    - school
    - workshop 1
    - workshop 2
    - workshop 3
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
            if not pd.isna(row["user_id"]):  # Check if user_id is not NaN
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
            if not pd.isna(row["school_id"]):  # Check if school_id is not NaN
                try:
                    df.at[idx, "school"] = School.objects.get(pk=row["school_id"]).name
                except School.DoesNotExist:
                    df.at[idx, "school"] = None
            elif row.get("other_school"):  # Fallback to other_school if available
                df.at[idx, "school"] = row["other_school"]
            else:
                df.at[idx, "school"] = None

            # Handle workshop registrations
            registrations = Registration.objects.filter(delegate_id=row["id"])
            for registration in registrations.values():
                if not pd.isna(registration["workshop_id"]):  # Check workshop_id
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
    Spreadsheet of workshop locations
    - workshop title
    - session
    - location (building + room number)
    """
    if not request.user.groups.filter(name="FACTAdmin").exists():
        return JsonResponse(
            {"message": "Must be admin to make this request"}, status=403
        )

    if request.method == "GET":
        workshops = Workshop.objects.all().values()

        df = pd.DataFrame.from_records(workshops)

        for idx, row in df.iterrows():
            location = Location.objects.get(pk=row["location_id"])
            df.at[idx, "location"] = f"{location.building} {location.room_num}"

        df.drop(
            ["id", "description", "facilitators", "location_id"], axis=1, inplace=True
        )

        file_path = "locations.xlsx"
        df.to_excel(file_path, index=False)

        response = FileResponse(open(file_path, "rb"))
        response["Content-Disposition"] = f'attachment; filename="{file_path}"'

        return response
    else:
        return JsonResponse({"message": "method not allowed"}, status=405)
