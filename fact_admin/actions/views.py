import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers as django_serializers

from fact_admin.models import RegistrationFlag

# set workshop locations
# get summary (sheet)
# get locations (sheet)
# reset database
# send email updates?


@csrf_exempt
def registration_flags(request):
    if request.method == "GET":
        data = django_serializers.serialize(
            "json", RegistrationFlag.objects.all()
        )
        return HttpResponse(data, content_type="application/json")
    else:
        return JsonResponse({"message": "method not allowed"}, status=405)


@csrf_exempt
def registration_flag_id(request, label):
    if request.method == "GET":
        flag = RegistrationFlag.objects.filter(label=label)

        if not flag.exists():
            return JsonResponse({"message": "Permission not found"}, status=404)

        return HttpResponse(
            django_serializers.serialize("json", flag),
            content_type="application/json",
        )
    if request.method == "PUT":
        # must be admin
        if not request.user.groups.filter(name="FACTAdmin").exists():
            return JsonResponse(
                {"message": "Must be admin to make this request"}, status=403
            )

        flag = RegistrationFlag.objects.filter(label=label)

        if not flag.exists():
            return JsonResponse({"message": "Permission not found"}, status=404)

        data = json.loads(request.body)
        value = data.get("value")

        if value == None or type(value) != bool:
            return JsonResponse({"message": "Must provide true/false value"})

        flag_obj = flag.first()
        flag_obj.value = value
        flag_obj.save()

        return HttpResponse(django_serializers.serialize("json", flag))
    else:
        return JsonResponse({"message": "method not allowed"}, status=405)
