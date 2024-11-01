import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from registration.models import Location
from django.core.exceptions import ValidationError
from django.core import serializers as django_serializers
import pandas as pd


# separate function to validate location data
def validate_location_data(data):
    required_fields = ["room_num", "building", "capacity", "session"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return False, {"message": f"Missing fields: {', '.join(missing_fields)}"}
    return True, None


@csrf_exempt
def locations(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON"}, status=400)

        is_valid, error_response = validate_location_data(data)
        if not is_valid:
            return JsonResponse(error_response, status=400)

        existing_location = Location.objects.filter(
            room_num=data["room_num"], building=data["building"]
        ).exists()

        if existing_location:
            return JsonResponse(
                {
                    "message": "Location already exists",
                    "location_id": existing_location.id,
                },
                status=409,
            )

        # location creation
        try:
            location = Location.objects.create(
                room_num=data["room_num"],
                building=data["building"],
                capacity=data["capacity"],
                session=data["session"],
            )
            location.save()

            data = django_serializers.serialize("json", [location])
            return HttpResponse(data, content_type="application/json", status=201)
        except ValidationError as e:
            return JsonResponse({"message": str(e)}, status=400)
        except:
            return JsonResponse({"message": "INVALID ERROR"}, status=405)
    elif request.method == "GET":
        data = django_serializers.serialize("json", Location.objects.all())
        return HttpResponse(data, content_type="application/json")
    else:
        return JsonResponse({"message": "Method not allowed"}, status=400)


@csrf_exempt
def location_id(request, id):
    if request.method == "GET":
        data = django_serializers.serialize("json", Location.objects.filter(id=id))
        return HttpResponse(data, content_type="application/json")
    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            location = Location.objects.get(id=id)

            room_num = data.get("room_num", location.room_num)
            building = data.get("building", location.building)
            capacity = data.get("capacity", location.capacity)
            session = data.get("session", location.session)

            if room_num and len(room_num) > 0:
                location.room_num = room_num
    
            if building and len(building) > 0:
                location.building = building

            if capacity and len(capacity) > 0:
                location.capacity = capacity

            if session and len(session) > 0:
                location.session = session

            location.save()
            data = django_serializers.serialize("json", [location])
            return HttpResponse(data, content_type="application/json")
        except Location.DoesNotExist:
            return JsonResponse({"message": "Location not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON"}, status=400)
    elif request.method == "DELETE":
        Location.objects.filter(id=id).delete()
        return JsonResponse({"message": "Success"})
    else:
        return JsonResponse({"message": "Method not allowed"}, status=405)


@csrf_exempt
def locations_bulk(request):
    if request.method == "POST":
        # must be admin
        if not request.user.groups.filter(name="FACTAdmin").exists():
            return JsonResponse(
                {"message": "Must be admin to make this request"}, status=403
            )

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
