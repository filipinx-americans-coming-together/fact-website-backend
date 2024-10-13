import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404

from registration import serializers
from registration.models import Location, Workshop
from django.core import serializers as django_serializers
from django.views.decorators.csrf import csrf_exempt


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
        data = django_serializers.serialize('json', Workshop.objects.all())
        return HttpResponse(data, content_type="application/json")
    else:
        return HttpResponse(status=400)

@csrf_exempt
def workshop_id(request, id):
    workshop = get_object_or_404(Workshop, location_id=id)

    if request.method == "GET":
        return HttpResponse(serializers.serialize_workshop(workshop), content_type="application/json")
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