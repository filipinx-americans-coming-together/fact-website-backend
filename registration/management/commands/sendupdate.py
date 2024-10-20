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
        delegate_df.set_index("id", inplace=True)

        users = User.objects.all().values()
        user_df = pandas.DataFrame(data=users)
        user_df.set_index("id", inplace=True)

        registrations = Registration.objects.all().values()
        registration_df = pandas.DataFrame(data=registrations)
        registration_df.set_index("id", inplace=True)

        session1 = Workshop.objects.filter(session=1).values()
        session1_df = pandas.DataFrame(data=session1)
        # session1_df.set_index("id", inplace=True)

        session2 = Workshop.objects.filter(session=2).values()
        session2_df = pandas.DataFrame(data=session2)
        # session2_df.set_index("id", inplace=True)

        session3 = Workshop.objects.filter(session=3).values()
        session3_df = pandas.DataFrame(data=session3)
        # session3_df.set_index("id", inplace=True)

        schools = School.objects.all().values()
        schools_df = pandas.DataFrame(data=schools)
        schools_df.set_index("id", inplace=True)

        for idx, row in delegate_df.iterrows():
            user_id = row["user_id"]
            all_data["first_name"].append(user_df.loc[user_id, "first_name"])
            all_data["last_name"].append(user_df.loc[user_id, "last_name"])
            all_data["pronouns"].append(row["pronouns"])
            all_data["year"].append(row["year"])
            all_data["school"].append(schools_df.loc[row["school_id"], "name"])
            all_data["email"].append(user_df.loc[user_id, "email"])

            # TODO finish this, needs workshops to have their own pk
            all_data["session_1"].append("")
            all_data["session_2"].append("")
            all_data["session_3"].append("")

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
