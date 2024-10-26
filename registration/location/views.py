import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from registration.models import Location
from django.core import serializers as django_serializers

import pandas as pd


@csrf_exempt
def location(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            obj1 = Location.objects.filter(room_num=data.get("room_num"))
            obj2 = Location.objects.filter(building=data.get("building"))
            if obj1.exists() and obj2.exists():
                if obj1[0].id == obj2[0].id:
                    return HttpResponse("Location already exists")

            location = Location.objects.create(
                room_num=data.get("room_num"),
                building=data.get("building"),
                capacity=data.get("capacity"),
            )

            location.save()

            return HttpResponse(status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    elif request.method == "GET":
        data = django_serializers.serialize("json", Location.objects.all())
        return HttpResponse(data, content_type="application/json")
    else:
        return HttpResponse(status=400)


@csrf_exempt
def location_id(request, id):
    if request.method == "GET":
        data = django_serializers.serialize("json", Location.objects.filter(id=id))
        return HttpResponse(data, content_type="application/json")
    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            location = Location.objects.get(id=id)

            location.room_num = data.get("room_num", location.room_num)
            location.building = data.get("building", location.building)
            location.capacity = data.get("capacity", location.capacity)

            location.save()
            return HttpResponse(status=200)
        except Location.DoesNotExist:
            return JsonResponse({"error": "Location not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    elif request.method == "DELETE":
        Location.objects.filter(id=id).delete()
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)


@csrf_exempt
def locations_bulk(request):
    if request.method == "POST":
        # must be admin
        # if not request.user.groups.filter(name="FACTAdmin").exists():
        #     return JsonResponse(
        #         {"message": "Must be admin to make this request"}, status=403
        #     )

        # must have no locations
        if len(Location.objects.all()) > 0:
            return JsonResponse(
                {"message": "Delete existing locations before attempting to upload"},
                status=409,
            )

        if "locations" not in request.FILES:
            return JsonResponse({"message": "Must include file"}, status=400)

        file = request.FILES["locations"]
        location_df = None

        try:
            location_df = pd.read_excel(file)
        except:
            return JsonResponse({"message": "Error reading file"}, status=400)

        location_df = location_df.drop_duplicates()
        # when loading in df, pandas will add ".#" to duplicate columns
        location_df.columns = [x.lower().split(".")[0] for x in location_df.columns]

        # validate data
        columns_set = set(location_df.columns)

        if len(columns_set) != len(location_df.columns):
            return JsonResponse({"message": "Duplicate column names"}, status=400)

        expected_columns = ["building", "room", "capacity", "session"]

        for i in range(len(expected_columns)):
            if expected_columns[i] not in columns_set:
                return JsonResponse(
                    {"message": f"Missing column {expected_columns[i]}"}, status=400
                )

        if location_df.isnull().values.any():
            return JsonResponse(
                {"message": "Missing values - make sure there are no empty cells"},
                status=400,
            )

        # make sure all session 1 2 3
        if len(location_df) != len(location_df[location_df["session"].isin([1, 2, 3])]):
            return JsonResponse(
                {
                    "message": "Data contains invalid session values - make sure all sessions are 1, 2, or 3"
                },
                status=400,
            )

        # create locations
        for index, row in location_df.iterrows():
            location = Location(
                building=row["building"],
                room_num=row["room"],
                capacity=row["capacity"],
                session=row["session"],
            )
            location.save()

        data = django_serializers.serialize("json", Location.objects.all())
        return HttpResponse(data, content_type="application/json")
    else:
        return JsonResponse({"message": "method not allowed"}, status=405)
