import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers as django_serializers
import pandas as pd

from registration.models import Delegate, NewSchool, School


@csrf_exempt
def schools(request):
    """
    Handle requests related to all schools

    GET - get all schools
    """

    if request.method == "GET":
        school_data = django_serializers.serialize(
            "json", School.objects.all().order_by("name")
        )

        return HttpResponse(school_data, content_type="application/json")
    else:
        return JsonResponse({"message": "Method not allowed"}, status=405)


@csrf_exempt
def new_schools(request):
    if request.method == "GET":
        data = django_serializers.serialize("json", NewSchool.objects.all())
        return HttpResponse(data, content_type="application/json")
    elif request.method == "POST":
        # must be admin
        if not request.user.groups.filter(name="FACTAdmin").exists():
            return JsonResponse(
                {"message": "Must be admin to make this request"}, status=403
            )

        data = json.loads(request.body)
        other_school = data.get("other_school")
        approved_name = data.get("approved_name")

        if approved_name == None or approved_name == "":
            return JsonResponse({"message": "Must provide approved name"})

        # create school object
        school = School.objects.filter(name=approved_name)

        if school:
            school = school.first()
        else:
            school = School(name=approved_name)
            school.save()

        # find delegates with other school and replace
        delegates = Delegate.objects.filter(other_school=other_school)
        delegates.update(other_school=None, school_id=school.pk)

        # remove new school object
        NewSchool.objects.filter(name=other_school).delete()

        return JsonResponse({"message": "success"}, status=200)
    else:
        return JsonResponse({"message": "Method not allowed"}, status=405)


@csrf_exempt
def schools_bulk(request):
    if request.method == "POST":
        # must be admin
        if not request.user.groups.filter(name="FACTAdmin").exists():
            return JsonResponse(
                {"message": "Must be admin to make this request"}, status=403
            )

        # must have no schools
        if School.objects.all().count() > 0:
            return JsonResponse(
                {"message": "Delete existing schools before attempting to upload"},
                status=409,
            )

        if "schools" not in request.FILES:
            return JsonResponse({"message": "Must include file"}, status=400)

        file = request.FILES["schools"]
        school_df = None

        try:
            school_df = pd.read_excel(file)
        except:
            return JsonResponse({"message": "Error reading file"}, status=400)

        school_df = school_df.drop_duplicates()
        # when loading in df, pandas will add ".#" to duplicate columns
        school_df.columns = [x.lower().split(".")[0] for x in school_df.columns]

        # validate data
        columns_set = set(school_df.columns)

        if len(columns_set) != len(school_df.columns):
            return JsonResponse({"message": "Duplicate column names"}, status=400)

        expected_columns = ["name"]

        for i in range(len(expected_columns)):
            if expected_columns[i] not in columns_set:
                return JsonResponse(
                    {"message": f"Missing column {expected_columns[i]}"}, status=400
                )

        if school_df.isnull().values.any():
            return JsonResponse(
                {"message": "Missing values - make sure there are no empty cells"},
                status=400,
            )

        # create schools
        for index, row in school_df.iterrows():
            school = School(name=row["name"])
            school.save()

        data = django_serializers.serialize("json", School.objects.all())
        return HttpResponse(data, content_type="application/json")
