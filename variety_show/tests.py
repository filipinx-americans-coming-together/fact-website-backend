import json

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.core import mail

from variety_show.models import Ticket


class PostTicket(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("variety_show:tickets")

    def test_rejects_bad_data(self):
        # no email
        response = self.client.post(
            self.url,
            json.dumps({"email": "", "first_name": "first", "last_name": "last"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Ticket.objects.all()), 0)

        response = self.client.post(
            self.url,
            json.dumps({"first_name": "first", "last_name": "last"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Ticket.objects.all()), 0)

        # invalid email
        response = self.client.post(
            self.url,
            json.dumps({"email": "email", "first_name": "first", "last_name": "last"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Ticket.objects.all()), 0)

        # no first name
        response = self.client.post(
            self.url,
            json.dumps(
                {"email": "email@email.com", "first_name": "", "last_name": "last"}
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Ticket.objects.all()), 0)

        response = self.client.post(
            self.url,
            json.dumps({"email": "email@email.com", "last_name": "last"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Ticket.objects.all()), 0)

        # no last name
        response = self.client.post(
            self.url,
            json.dumps(
                {"email": "email@email.com", "first_name": "first", "last_name": ""}
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Ticket.objects.all()), 0)

        response = self.client.post(
            self.url,
            json.dumps({"email": "email@email.com", "first_name": "first"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Ticket.objects.all()), 0)

    def test_creates_ticket(self):
        email = "email@email.com"
        first_name = "first"
        last_name = "last"

        response = self.client.post(
            self.url,
            json.dumps(
                {"email": email, "first_name": first_name, "last_name": last_name}
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Ticket.objects.all()), 1)

        # data matches
        data = response.json()[0]["fields"]
        self.assertEqual(data["email"], email)
        self.assertEqual(data["first_name"], first_name)
        self.assertEqual(data["last_name"], last_name)

        # sends email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Variety Show Ticket", mail.outbox[0].subject)

class GetTickets(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("variety_show:tickets")

        group = Group.objects.create(name="FACTAdmin")

        self.username = "admin-user"
        self.password = "admin-pass"
        user = User.objects.create(username=self.username)
        user.set_password(self.password)
        user.groups.add(group)
        user.save()

        self.non_admin_username = "non-admin-user"
        self.non_admin_password = "non-admin-pass"
        user = User.objects.create(username=self.non_admin_username)
        user.set_password(self.non_admin_password)

    def test_rejects_non_admin(self):
        # no user
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

        # non admin
        self.client.login(
            username=self.non_admin_username, password=self.non_admin_password
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_returns_tickets(self):
        tickets = []

        for i in range(5):
            tickets.append(
                Ticket.objects.create(
                    first_name=f"first {i}",
                    last_name=f"last {i}",
                    email=f"email{i}@email.com",
                )
            )

        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.url)
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), len(Ticket.objects.all()))

        for i in range(len(tickets)):
            self.assertEqual(data[i]["fields"]["first_name"], tickets[i].first_name)
            self.assertEqual(data[i]["fields"]["last_name"], tickets[i].last_name)
            self.assertEqual(data[i]["fields"]["email"], tickets[i].email)
