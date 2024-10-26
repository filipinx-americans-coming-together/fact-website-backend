import json
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core import serializers

from fact_admin.models import Notification


def notification(request):
    """
    Process requests for single notification

    POST - create notification, expect { message: string, expiration: ISO8601 date string }
    """
    if request.method == "POST":
        user = request.user

        # make sure user is allowed
        if not user.groups.filter(name="FACTAdmin").exists():
            return JsonResponse(
                {"message": "Must be admin to make this request"}, status=403
            )

        # get data
        data = json.loads(request.body)

        message = data.get("message")
        expiration = data.get("expiration")

        # check data
        if not message or len(message) < 10:
            JsonResponse({"message": "Enter a valid message"}, status=400)

        if not expiration:
            JsonResponse({"message": "Please provide expiration date/time"}, status=400)

        try:
            expiration = timezone.datetime.fromisoformat(expiration)
        except:
            JsonResponse(
                {"message": "Expiration could not be converted to valid date/time"},
                status=400,
            )

        # create object
        notification = Notification(message=message, expiration=expiration)
        notification.save()

        return HttpResponse(
            serializers.serialize(
                "json", Notification.objects.filter(id=notification.pk)
            ),
            content_type="application/json",
        )
    else:
        return HttpResponse(status=405)


def notifications(request):
    if request.method == "GET":
        # get objects that are not expired
        notifications = Notification.objects.filter(
            expiration__gt=timezone.make_aware(timezone.datetime.now())
        )
        return HttpResponse(
            serializers.serialize("json", notifications),
            content_type="application/json",
        )
    else:
        return HttpResponse(status=405)
