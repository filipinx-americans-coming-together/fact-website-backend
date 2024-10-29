import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers as django_serializers

from fact_admin.models import RegistrationPermission

# set workshop locations
# get summary (sheet)
# get locations (sheet)
# reset database
# send email updates?


@csrf_exempt
def registration_permissions(request):
    if request.method == "GET":
        data = django_serializers.serialize(
            "json", RegistrationPermission.objects.all()
        )
        return HttpResponse(data, content_type="application/json")
    else:
        return JsonResponse({"message": "method not allowed"}, status=405)


@csrf_exempt
def registration_permission_id(request, id):
    if request.method == "GET":
        permission = RegistrationPermission.objects.filter(pk=id)

        if not permission.exists():
            return JsonResponse({"message": "Permission not found"}, status=404)

        return HttpResponse(
            django_serializers.serialize("json", permission),
            content_type="application/json",
        )
    if request.method == "PUT":
        # must be admin
        if not request.user.groups.filter(name="FACTAdmin").exists():
            return JsonResponse(
                {"message": "Must be admin to make this request"}, status=403
            )
        
        permission = RegistrationPermission.objects.filter(pk=id)

        if not permission.exists():
            return JsonResponse({"message": "Permission not found"}, status=404)

        data = json.loads(request.body)
        value = data.get("value")

        if (
            value == None
            or value == ""
            or value.lower().strip() not in ["true", "false"]
        ):
            return JsonResponse({"message": "Must provide true/false value"})

        value = value.lower().strip()

        permission.first().value = True if value == "true" else False
        permission.save()

        return HttpResponse(django_serializers.serialize("json", permission))
    else:
        return JsonResponse({"message": "method not allowed"}, status=405)