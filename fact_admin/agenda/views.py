import json
from django.http import JsonResponse
from fact_admin.models import AgendaItem, Session
from django.core import serializers as django_serializers

# TODO do we need endpoints for editing session info directly/single sessions?


def sessions(request):
    if request.method == "GET":
        data = django_serializers.serialize("json", Session.objects.all())
        return JsonResponse(data, safe=False)

    else:
        return JsonResponse({"message": "method not allowed"}, status=405)


def agenda_items(request):
    if request.method == "GET":
        data = django_serializers.serialize("json", AgendaItem.objects.all())
        return JsonResponse(data, safe=False)

    else:
        return JsonResponse({"message": "method not allowed"}, status=405)


def agenda_items_id(request, id):
    if request.method == "GET":
        data = AgendaItem.objects.filter(pk=id)

        if not data.exists():
            return JsonResponse(
                {"message": f"Agenda item with id {id} does not exist"}, status=404
            )

        return JsonResponse(django_serializers.serialize("json", data), safe=False)

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
                {"message": "Must provide title, start_time, end_time, and building"},
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

        return JsonResponse(
            django_serializers.serialize(
                AgendaItem.objects.filter(pk=new_agenda_item.pk)
            ),
            safe=False
        )

    elif request.method == "DELETE":
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
