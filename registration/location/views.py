import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from registration.models import Location
from django.core.exceptions import ValidationError
from django.core import serializers as django_serializers

# separate function to validate location data
def validate_location_data(data):
    required_fields = ["room_num", "building", "capacity"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return False, {"error": f"Missing fields: {', '.join(missing_fields)}"}
    return True, None

@csrf_exempt
def location(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        is_valid, error_response = validate_location_data(data)
        if not is_valid:
            return JsonResponse(error_response, status=400)

        existing_location = Location.objects.filter(
            room_num=data["room_num"], building=data["building"]
        ).first()

        if existing_location:
            return JsonResponse(
                {"message": "Location already exists", "location_id": existing_location.id}, 
                status=409
            )

        # location creation
        try:
            location = Location.objects.create(
                room_num=data["room_num"],
                building=data["building"],
                capacity=data["capacity"]
            )
            return JsonResponse(
                {"message": "Location created", "location_id": location.id}, 
                status=201
            )
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == "GET":
        locations = Location.objects.all()
        data = django_serializers.serialize('json', locations)
        return JsonResponse({"locations": json.loads(data)}, safe=False, status=200)

    return JsonResponse({"error": "INVALID ERROR"}, status=405)

@csrf_exempt
def location_id(request, id):
    if request.method == "GET":
        data = django_serializers.serialize('json', Location.objects.filter(id=id))
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