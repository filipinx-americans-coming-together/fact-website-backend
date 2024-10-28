import datetime
import json
import pytz

from django.http import HttpResponse, JsonResponse
import pandas as pd
from fact_admin.models import AgendaItem
from django.core import serializers as django_serializers
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone


@csrf_exempt
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

        if not title or not start_time or not end_time:
            return JsonResponse(
                {"message": "Must provide title, start time, end time, and building"},
                status=400,
            )

        if title == "" or start_time == "" or end_time == "":
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
        )

        # note this just ignores malformed session data
        if len(session_num) > 0 and session_num in ["1", "2", "3"]:
            new_agenda_item.session_num = int(session_num)

        new_agenda_item.save()

        data = django_serializers.serialize(
            "json", AgendaItem.objects.filter(pk=new_agenda_item.pk)
        )
        return HttpResponse(data, content_type="application/json")

    else:
        return JsonResponse({"message": "method not allowed"}, status=405)


@csrf_exempt
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


@csrf_exempt
def agenda_items_bulk(request):
    if request.method == "POST":
        # make sure user is allowed
        if not request.user.groups.filter(name="FACTAdmin").exists():
            return JsonResponse(
                {"message": "Must be admin to make this request"}, status=403
            )

        # must have no agenda items
        if len(AgendaItem.objects.all()) > 0:
            return JsonResponse(
                {"message": "Delete existing agenda items before attempting to upload"},
                status=409,
            )

        if "agenda" not in request.FILES:
            return JsonResponse({"message": "Must include file"}, status=400)

        file = request.FILES["agenda"]
        agenda_df = None

        try:
            agenda_df = pd.read_excel(file)
        except:
            return JsonResponse({"message": "Error reading file"}, status=400)

        agenda_df = agenda_df.drop_duplicates()
        # when loading in df, pandas will add ".#" to duplicate columns
        agenda_df.columns = [x.lower().split(".")[0] for x in agenda_df.columns]

        # validate data
        columns_set = set(agenda_df.columns)

        if len(columns_set) != len(agenda_df.columns):
            return JsonResponse({"message": "Duplicate column names"}, status=400)

        expected_columns = [
            "title",
            "date",
            "start_time",
            "end_time",
            "building",
            "room_num",
            "session_num",
        ]

        for i in range(len(expected_columns)):
            if expected_columns[i] not in columns_set:
                return JsonResponse(
                    {"message": f"Missing column '{expected_columns[i]}'"}, status=400
                )

        # check data
        for idx, row in agenda_df.iterrows():
            if row["start_time"] > row["end_time"]:
                return JsonResponse(
                    {"message": "Start times can not be after end times"}, status=400
                )

        timezone = pytz.timezone("America/Chicago")

        for idx, row in agenda_df.iterrows():
            start_datetime = timezone.localize(
                datetime.datetime.combine(row["date"], row["start_time"])
            )

            end_datetime = timezone.localize(
                datetime.datetime.combine(row["date"], row["end_time"])
            )

            new_agenda_item = AgendaItem(
                title=row["title"],
                building=row["building"],
                room_num=row["room_num"],
                start_time=start_datetime,
                end_time=end_datetime,
            )

            # note this just ignores malformed session data
            if row["session_num"] and row["session_num"] in [1, 2, 3]:
                new_agenda_item.session_num = int(row["session_num"])

            new_agenda_item.save()

        data = django_serializers.serialize(
            "json", AgendaItem.objects.all().order_by("start_time")
        )
        return HttpResponse(data, content_type="application/json")
    else:
        return JsonResponse({"message": "method not allowed"}, status=405)
