from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers as django_serializers
import pandas as pd

from registration.models import School


@csrf_exempt
def schools(request):
    """
    Handle requests related to all schools

    GET - get all schools
    """

    if request.method == "GET":
        school_data = django_serializers.serialize("json", School.objects.all().order_by("name"))

        return HttpResponse(school_data, content_type="application/json")
    else:
        return HttpResponse(status=405)


@csrf_exempt
def schools_bulk(request):
    if request.method == "POST":
        # must be admin
        # if not request.user.groups.filter(name="FACTAdmin").exists():
        #     return JsonResponse(
        #         {"message": "Must be admin to make this request"}, status=403
        #     )

        # must have no schools
        if len(School.objects.all()) > 0:
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
            school = School(
                name=row["name"]
            )
            school.save()

        data = django_serializers.serialize("json", School.objects.all())
        return HttpResponse(data, content_type="application/json")
