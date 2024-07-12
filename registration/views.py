from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.core import serializers
from registration.models import Workshop, Location
from django.views.decorators.csrf import csrf_exempt

import json

@csrf_exempt
def workshop(request):
    if request.method == "POST":
        workshop = Workshop.objects.create(title=request.POST.get("title"), description=request.POST.get("description"), facilitators=request.POST.get("facilitators"), location=request.POST.get("location"), session=request.POST.get("session"))
        workshop.save()
        
        return HttpResponse(status=200)
    elif request.method == "GET":
        data = serializers.serialize('json', Workshop.objects.all())
        return HttpResponse(data, content_type="application/json")
    else:
        return HttpResponse(status=400)
    
@csrf_exempt
def workshop_id(request, id):
    if request.method == "GET":
        data = serializers.serialize('json', Workshop.objects.filter(id=id))
        return HttpResponse(data, content_type="application/json")
    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            Workshop = Workshop.objects.get(id=id)
            Workshop.title = data.get("title", Workshop.title)
            Workshop.description = data.get("description", Workshop.description)
            Workshop.facilitators = data.get("facilitators", Workshop.facilitators)
            Workshop.location = data.get("location", Workshop.location)
            Workshop.session = data.get("session", Workshop.session)
            Workshop.save()
            return HttpResponse(status=200)
        except Workshop.DoesNotExist:
            return JsonResponse({"error": "Workshop not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    elif request.method == "DELETE":
        Workshop.objects.filter(id=id).delete()
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)

@csrf_exempt
def location(request):
    if request.method == "POST":
        obj1 = Location.objects.filter(room_num=request.POST.get("room_num"))
        obj2 = Location.objects.filter(building=request.POST.get("building"))
        if (obj1.exists() and obj2.exists()):
            if (obj1[0].id == obj2[0].id):
                return HttpResponse("Location already exists")

        location = Location.objects.create(room_num=request.POST.get("room_num"), building=request.POST.get("building"), capacity=request.POST.get("capacity"))
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