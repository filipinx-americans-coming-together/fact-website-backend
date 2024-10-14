import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from registration.models import Location
from django.core import serializers as django_serializers

@csrf_exempt
def location(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            obj1 = Location.objects.filter(room_num=data.get("room_num"))
            obj2 = Location.objects.filter(building=data.get("building"))
            if (obj1.exists() and obj2.exists()):
                if (obj1[0].id == obj2[0].id):
                    return HttpResponse("Location already exists")

            location = Location.objects.create(
                room_num=data.get("room_num"),
                building=data.get("building"),
                capacity=data.get("capacity")
            )
            
            location.save()

            return HttpResponse(status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    elif request.method == "GET":
        data = django_serializers.serialize('json', Location.objects.all())
        return HttpResponse(data, content_type="application/json")
    else:
        return HttpResponse(status=400)

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