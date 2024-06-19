from django.shortcuts import render, HttpResponse
from django.core import serializers
from registration.models import Workshop

import json

def workshop(request):
    if request.method == "POST":
        # get data
        workshop_title = request.POST.get("workshop_title")

        # create workshop
        workshop = Workshop.objects.create(workshop_title=workshop_title)
        workshop.save()
        
        return HttpResponse("workshop created: " + str(workshop))
    elif request.method == "GET":
        data = serializers.serialize('json', Workshop.objects.all())
        return HttpResponse(data, content_type="application/json")
    elif request.method == "DELETE":
        id = request.POST.get("workshop_id")

        Workshop.objects.filter(id=id).delete()
        return HttpResponse(f"workshop {id} deleted")
    else:
        return HttpResponse(status=400)