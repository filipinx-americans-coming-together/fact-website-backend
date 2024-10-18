import json

from django.http import HttpResponse, JsonResponse
from fact_admin.models import AgendaItem
from django.core import serializers as django_serializers
from django.utils.dateparse import parse_datetime


def agenda_items(request):
    if request.method == "GET":
        data = django_serializers.serialize(
            "json", AgendaItem.objects.all().order_by("start_time")
        )
        return HttpResponse(data, content_type="application/json")
    elif request.method == "POST":
        # make sure user is allowed
        if not request.user.groups.filter(name="FACTAdmin").exists():
            return JsonResponse(
                {"message": "Must be admin to make this request"}, status=403
            )

        data = json.loads(request.body)
        title = data.get("title")
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        building = data.get("building")
        room_num = data.get("room_num")
        session_num = data.get("session_num")

        if not title or not start_time or not end_time or not building:
            return JsonResponse(
                {"message": "Must provide title, start time, end time, and building"},
                status=400,
            )

        if title == "" or start_time == "" or end_time == "" or building == "":
            return JsonResponse(
                {"message": "Must provide title, start time, end time, and building"},
                status=400,
            )

        start_time = parse_datetime(start_time)
        end_time = parse_datetime(end_time)

        if start_time > end_time:
            return JsonResponse(
                {"message": "End time can not be before start time"},
                status=400,
            )

        new_agenda_item = AgendaItem(
            title=title,
            building=building,
            room_num=room_num,
            start_time=start_time,
            end_time=end_time,
            session_num=session_num,
        )
        new_agenda_item.save()

        data = django_serializers.serialize(
            "json", AgendaItem.objects.filter(pk=new_agenda_item.pk)
        )
        return HttpResponse(data, content_type="application/json")

    else:
        return JsonResponse({"message": "method not allowed"}, status=405)


def agenda_items_id(request, id):
    if request.method == "DELETE":
        # make sure user is allowed
        if not request.user.groups.filter(name="FACTAdmin").exists():
            return JsonResponse(
                {"message": "Must be admin to make this request"}, status=403
            )

        if not AgendaItem.objects.filter(pk=id).exists():
            return JsonResponse({"message": "Agenda item not found"}, status=404)

        AgendaItem.objects.get(pk=id).delete()

        return JsonResponse({"message": "Delete success"})

    else:
        return JsonResponse({"message": "method not allowed"}, status=405)
