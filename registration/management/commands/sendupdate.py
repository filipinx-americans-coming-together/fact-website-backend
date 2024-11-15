import os
import pandas
import environ

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.mail import EmailMessage

from registration.models import Delegate, Registration, School, Workshop

env = environ.Env()
environ.Env.read_env()


class Command(BaseCommand):
    def handle(self, *args, **options):
        all_data = {
            "first_name": [],
            "last_name": [],
            "pronouns": [],
            "year": [],
            "school": [],
            "email": [],
            "session_1": [],
            "session_2": [],
            "session_3": [],
        }

        # create data frames
        delegates = Delegate.objects.all().values()
        delegate_df = pandas.DataFrame(data=delegates)

        if len(delegate_df) > 0:
            delegate_df.set_index("id", inplace=True)

        users = User.objects.all().values()
        user_df = pandas.DataFrame(data=users)

        if len(user_df) > 0:
            user_df.set_index("id", inplace=True)

        schools = School.objects.all().values()
        schools_df = pandas.DataFrame(data=schools)

        if len(schools_df) > 0:
            schools_df.set_index("id", inplace=True)

        for idx, row in delegate_df.iterrows():
            user_id = row["user_id"]
            all_data["first_name"].append(user_df.loc[user_id, "first_name"])
            all_data["last_name"].append(user_df.loc[user_id, "last_name"])
            all_data["pronouns"].append(row["pronouns"])
            all_data["year"].append(row["year"])

            if not pandas.isna(row["school_id"]):
                all_data["school"].append(schools_df.loc[row["school_id"], "name"])
            elif row["other_school"]:
                all_data["school"].append(row["other_school"])
            else:
                all_data["school"].append("")

            all_data["email"].append(user_df.loc[user_id, "email"])

            registrations = Registration.objects.filter(delegate_id=idx).values()

            for registration in registrations:
                workshop = Workshop.objects.get(pk=registration["workshop_id"])

                # assumes workshops have session 1, 2, or 3
                key = f"session_{workshop.session}"
                all_data[key].append(workshop.title)

        # save file
        final_df = pandas.DataFrame(data=all_data)

        base_path = "./registration/management/commands/data"
        os.mkdir(base_path)
        file_name = "delegate_data.xlsx"
        path = f"{base_path}/{file_name}"

        final_df.to_excel(path, index=False)

        # email
        subject = "FACT 2024 Automated Registration Update"
        message = "Registration spreadsheet attached"
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

        self.stdout.write(self.style.SUCCESS("Spreadsheet sent successfully"))

        # clean up
        os.remove(path)
        os.rmdir(base_path)
