import os
import pandas
import environ

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.mail import EmailMessage

from registration.models import Delegate, Location, Registration, School, Workshop

env = environ.Env()
environ.Env.read_env()


def setLocations(session_num):
    # get/sort workshops
    workshops = Workshop.objects.filter(session=session_num).values()
    workshop_df = pandas.DataFrame(data=workshops)

    registrations = []
    for idx, row in workshop_df.iterrows():
        registrations.append(len(Registration.objects.filter(workshop_id=idx)))

    workshop_df["registrations"] = registrations
    workshop_df = workshop_df.sort_values("registrations", ascending=False)

    # get/sort locations
    locations = Location.objects.filter(session=session_num).values()
    location_df = pandas.DataFrame(data=locations)
    location_df = location_df.sort_values("capacity", ascending=False)

    if len(location_df) < len(workshop_df):
        return False

    # verify locations work
    for i in range(len(workshop_df)):
        if workshop_df.iloc[i]["registrations"] > location_df.iloc[i]["capacity"]:
            return False

    # clear locations
    for i in range(len(workshop_df)):
        workshop_id = workshop_df.iloc[i]["id"]
        workshop = Workshop.objects.get(pk=workshop_id)

        workshop.location = None
        workshop.save()

    # place locations
    for i in range(len(workshop_df)):
        workshop_id = workshop_df.iloc[i]["id"]
        location_id = location_df.iloc[i]["id"]

        workshop = Workshop.objects.get(pk=workshop_id)
        location = Location.objects.get(pk=location_id)

        workshop.location = location
        workshop.save()

    return True


class Command(BaseCommand):
    def handle(self, *args, **options):
        successes = [False] * 3

        for i in range(3):
            successes[i] = setLocations(i + 1)

        # save file
        workshops = Workshop.objects.all().order_by("session").values()
        workshop_df = pandas.DataFrame(data=workshops)

        location_data = {"building": [], "room_num": [], "capacity": []}

        for idx, row in workshop_df.iterrows():
            location = Location.objects.get(id=row["location_id"])

            location_data["building"].append(location.building)
            location_data["room_num"].append(location.room_num)
            location_data["capacity"].append(location.capacity)

        location_df = pandas.DataFrame(data=location_data)
        final_df = pandas.concat([workshop_df, location_df], axis=1)

        base_path = "./registration/management/commands/data"
        os.mkdir(base_path)
        file_name = "workshop_locations.xlsx"
        path = f"{base_path}/{file_name}"

        final_df.to_excel(path, index=False)

        # email
        subject = "FACT 2024 Automated Workshop Location Update"
        message = "Workshop location data attached."
        from_email = env("EMAIL_HOST_USER")
        recipient_list = ["fact.it@psauiuc.org"]

        email = EmailMessage(subject, message, from_email, recipient_list)

        with open(path, "rb") as file:
            email.attach(
                file_name,
                file.read(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        email.send()

        self.stdout.write(self.style.SUCCESS("Workshop Location update success"))

        # clean up
        os.remove(path)
        os.rmdir(base_path)
