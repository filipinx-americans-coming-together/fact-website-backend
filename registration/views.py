from django.shortcuts import HttpResponse, get_object_or_404
from django.http import JsonResponse
from django.core import serializers
from registration.models import Workshop, Location
from django.views.decorators.csrf import csrf_exempt

import json

"""
PROBLEMS WITH CODE:
1. Remove csrf_exempt from all functions
"""

@csrf_exempt
def workshop(request):
    # Note: Does not account for when attributes are missing in POST request
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            location = get_object_or_404(Location, id=data.get("location"))

            w = Workshop.objects.filter(title=data.get("title"))

            if (w.exists()):
                if (w[0].session == data.get("session")):    
                    return HttpResponse("Workshop in current session already exists")

            workshop = Workshop(
                title=data.get("title"),
                description=data.get("description"),
                facilitators=data.get("facilitators"),
                location=location,
                session=data.get("session")
            )

            workshop.save()
            return HttpResponse(status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    elif request.method == "GET":
        data = serializers.serialize('json', Workshop.objects.all())
        return HttpResponse(data, content_type="application/json")
    else:
        return HttpResponse(status=400)

@csrf_exempt
def workshop_id(request, id):
    workshop = get_object_or_404(Workshop, location_id=id)

    if request.method == "GET":
        data = serializers.serialize('json', [workshop])
        return HttpResponse(data, content_type="application/json")
    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            location = get_object_or_404(Location, id=data.get("location"))

            workshop.title = data.get("title", workshop.title)
            workshop.description = data.get("description", workshop.description)
            workshop.facilitators = data.get("facilitators", workshop.facilitators)
            workshop.location = location
            workshop.session = data.get("session", workshop.session)

            workshop.save()
            return HttpResponse(status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    elif request.method == "DELETE":
        workshop.delete()
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)

@csrf_exempt
def location(request):
    if request.method == "POST":
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
    elif request.method == "GET":
        data = serializers.serialize('json', Location.objects.all())
        return HttpResponse(data, content_type="application/json")
    else:
        return HttpResponse(status=400)

@csrf_exempt
def location_id(request, id):
    if request.method == "GET":
        data = serializers.serialize('json', Location.objects.filter(id=id))
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