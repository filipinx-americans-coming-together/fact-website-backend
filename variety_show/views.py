import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email

from variety_show.models import Ticket


@csrf_exempt
def tickets(request):
    if request.method == "GET":
        # must be admin
        if not request.user.groups.filter(name="FACTAdmin").exists():
            return JsonResponse(
                {"message": "Must be admin to make this request"}, status=403
            )

        data = serializers.serialize("json", Ticket.objects.all())
        return HttpResponse(data, content_type="application/json")
    elif request.method == "POST":
        data = json.loads(request.body)
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")

        if not first_name or first_name == "":
            return JsonResponse({"message": "Must provide first name"}, status=400)

        if not last_name or last_name == "":
            return JsonResponse({"message": "Must provide first name"}, status=400)

        if not email or email == "":
            return JsonResponse({"message": "Must provide first name"}, status=400)

        try:
            validate_email(email)
        except:
            return JsonResponse({"message": "Invalid email"}, status=400)

        # TODO get payment proof

        # TODO send ticket (with barcode?? or something idk)

        ticket = Ticket.objects.create(
            email=email, first_name=first_name, last_name=last_name
        )

        data = serializers.serialize(
            "json",
            Ticket.objects.filter(pk=ticket.pk),
        )
        return HttpResponse(data, content_type="application/json")

    else:
        return JsonResponse({"message": "method not allowed"}, status=405)
