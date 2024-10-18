import json

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from registration.models import Delegate, Location, Registration, Workshop


class WorkshopAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.location = Location.objects.create(
            room_num="Test Room", building="Test Building", capacity=100
        )
        self.workshop = Workshop.objects.create(
            title="Test Workshop",
            description="Test Description",
            facilitators=["Facilitator 1", "Facilitator 2"],
            location=self.location,
            session=1,
        )
        self.workshop_url = reverse("registration:workshop")
        self.workshop_id_url = reverse(
            "registration:workshop_id", kwargs={"id": self.workshop.pk}
        )

    def test_post_workshop(self):
        data = {
            "title": "New Workshop",
            "description": "New Description",
            "facilitators": ["Facilitator 1", "Facilitator 2"],
            "location": self.location.id,
            "session": 1,
        }
        response = self.client.post(
            self.workshop_url, json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

    # def test_post_workshop_missing_attribute(self):
    #     data = {
    #         "title": "New Workshop",
    #         "description": "New Description",
    #         "facilitators": [
    #             "Facilitator 1",
    #             "Facilitator 2"
    #         ],
    #         "location": self.location.id
    #     }
    #     response = self.client.post(self.workshop_url, json.dumps(data), content_type="application/json")
    #     self.assertEqual(response.status_code, 400)

    def test_post_workshop_invalid_json(self):
        response = self.client.post(
            self.workshop_url, "Invalid JSON", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Invalid JSON", status_code=400)

    def test_get_workshop(self):
        response = self.client.get(self.workshop_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Workshop")

    def test_get_workshop_id(self):
        response = self.client.get(self.workshop_id_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Workshop")

    def test_put_workshop_id(self):
        data = {
            "title": "Updated Workshop",
            "description": "Updated Description",
            "facilitators": ["Updated Facilitator 1", "Updated Facilitator 2"],
            "location": self.location.id,
            "session": 1,
        }
        response = self.client.put(
            self.workshop_id_url, json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.workshop.refresh_from_db()
        self.assertEqual(self.workshop.title, "Updated Workshop")

    def test_delete_workshop_id(self):
        response = self.client.delete(self.workshop_id_url)
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(Workshop.DoesNotExist):
            Workshop.objects.get(pk=self.workshop.pk)

    def test_post_workshop_already_exists(self):
        data = {
            "title": "Test Workshop",
            "description": "Another Description",
            "facilitators": ["Facilitator 1", "Facilitator 2"],
            "location": self.location.id,
            "session": 1,
        }
        response = self.client.post(
            self.workshop_url, json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Workshop in current session already exists")


class WorkshopRegistrations(TestCase):
    # TODO fix/remove location after merge

    def setUp(self):
        self.client = Client()

    def test_404s_no_workshop(self):
        location = Location.objects.create(
            room_num="A", building="building", capacity=10, session=1
        )

        workshop = Workshop.objects.create(
            title="workshop title",
            description="workshop description",
            facilitators="[fac1, fac2]",
            session=1,
            location=location,
        )

        response = self.client.get(
            reverse(
                "registration:workshop_registration", kwargs={"id": workshop.pk + 1}
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_returns_num_registrations(self):
        location = Location.objects.create(
            room_num="A", building="building", capacity=10, session=1
        )

        workshop = Workshop.objects.create(
            title="workshop title",
            description="workshop description",
            facilitators="[fac1, fac2]",
            session=1,
            location=location,
        )

        expected_registrations = 3

        for i in range(expected_registrations):
            user = User.objects.create(username=f"user{i}")
            delegate = Delegate.objects.create(user=user, year="")

            Registration.objects.create(workshop=workshop, delegate=delegate)

        response = self.client.get(
            reverse(
                "registration:workshop_registration", kwargs={"id": workshop.pk}
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["num_registrations"], expected_registrations)
