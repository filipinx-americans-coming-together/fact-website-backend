import json
import pandas as pd

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

            location = None
            if "location" in data:
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
def workshops_bulk(request):
    """
    Process many workshops via file upload
    Expects multipart/form data (to be able to accept files)
    """
    if request.method == "POST":
        # must be admin
        if not request.user.groups.filter(name="FACTAdmin").exists():
            return JsonResponse(
                {"message": "Must be admin to make this request"}, status=403
            )

        # must have no workshops
        if len(Workshop.objects.all()) > 0:
            return JsonResponse({"message": "Delete existing workshops before attempting to upload"}, status=409)
        
        if "workshops" not in request.FILES:
            return JsonResponse({"message": "Must include file"}, status=400)

        file = request.FILES["workshops"]
        workshop_df = None

        try:
            workshop_df = pd.read_excel(file)
        except:
            return JsonResponse({"message": "Error reading file"}, status=400)

        workshop_df = workshop_df.drop_duplicates()
        # when loading in df, pandas will add ".#" to duplicate columns
        workshop_df.columns = [x.lower().split(".")[0] for x in workshop_df.columns]

        # validate data
        columns_set = set(workshop_df.columns)

        if len(columns_set) != len(workshop_df.columns):
            return JsonResponse({"message": "Duplicate column names"}, status=400)

        expected_columns = ["title", "session", "description", "facilitators"]
        
        for i in range(len(expected_columns)):
            if expected_columns[i] not in columns_set:
                return JsonResponse({"message": f"Missing column {expected_columns[i]}"}, status=400)
            
        if workshop_df.isnull().values.any():
            return JsonResponse({"message": "Missing values - make sure there are no empty cells"}, status=400)

        # check sessions and locations
        workshop_count = {
            1: 0,
            2: 0,
            3: 0
        }

        valid_sessions = set([1, 2, 3])

        for idx, rows in workshop_df.iterrows():
            if rows["session"] not in valid_sessions:
                return JsonResponse({"message": f"{rows['session']} is not a valid session number"}, status=400)
            
            workshop_count[rows["session"]] += 1
        
        for i in range(1, 4):
            if workshop_count[i] > len(Location.objects.filter(session=i)):
                return JsonResponse({"message": f"Not enough locations for given workshops in session {i}"}, status=409)

        # save workshops
        for index, row in workshop_df.iterrows():
            workshop = Workshop(
                            title=row["title"],
                            description=row["description"],
                            facilitators=row["facilitators"],
                            session=row["session"]
                        )

            workshop.save()

        # set locations

        data = django_serializers.serialize('json', Workshop.objects.all())

        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({"message": "method not allowed"}, status=405)

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