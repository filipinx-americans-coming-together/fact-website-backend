import json
import pandas as pd

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from registration.models import Location, Workshop

class WorkshopAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.location = Location.objects.create(room_num="Test Room", building="Test Building", capacity=100)
        self.workshop = Workshop.objects.create(
            title="Test Workshop",
            description="Test Description",
            facilitators=[
                "Facilitator 1",
                "Facilitator 2"
            ],
            location=self.location,
            session=1
        )
        self.workshop_url = reverse('registration:workshop')
        self.workshop_id_url = reverse('registration:workshop_id', kwargs={'id': self.workshop.pk})

    def test_post_workshop(self):
        data = {
            "title": "New Workshop",
            "description": "New Description",
            "facilitators": [
                "Facilitator 1",
                "Facilitator 2"
            ],
            # "location": self.location.id,
            "session": 1
        }
        response = self.client.post(self.workshop_url, json.dumps(data), content_type="application/json")
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
        response = self.client.post(self.workshop_url, "Invalid JSON", content_type="application/json")
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
            "facilitators": [
                "Updated Facilitator 1",
                "Updated Facilitator 2"
            ],
            "location": self.location.id,
            "session": 1
        }
        response = self.client.put(self.workshop_id_url, json.dumps(data), content_type="application/json")
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
            "facilitators": [
                "Facilitator 1",
                "Facilitator 2"
            ],
            "location": self.location.id,
            "session": 1
        }
        response = self.client.post(self.workshop_url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Workshop in current session already exists")

class WorkshopPOSTBulk(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("registration:workshops_bulk")

        # files
        titles = ["workshop 1", "workshop 2", "workshop 3"]
        sessions = [1, 2, 3]
        descriptions = ["description 1", "description 2", "description 3"]
        facilitators = ["fac1, fac11", "fac2", "fac3"]
        data = {"title": titles, "Session": sessions, "description": descriptions, "facilitators": facilitators}
        df = pd.DataFrame(data)

        self.good_workshops = "./registration/workshop/data/good_workshops.xlsx"
        df.to_excel(self.good_workshops, index=False)
        

    def test_not_admin(self):
        with open(self.good_workshops, 'rb') as f:
            workshop_file = SimpleUploadedFile(
                name='good_workshops.xlsx',
                content=f.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        response = self.client.post(self.url, {"workshops": workshop_file})

        self.assertEqual(response.status_code, 403)
        self.assertEquals(len(Workshop.objects.all()), 0)

    def test_no_file(self):
        pass

    def test_workshops_exist(self):
        pass

    def test_no_file(self):
        pass

    def test_invalid_file(self):
        pass

    def test_duplicate_cols(self):
        pass

    def test_not_enough_locations(self):
        pass

    def test_missing_cols(self):
        pass

    def test_missing_vals(self):
        pass

    def test_invalid_session(self):
        pass

    def test_creates_workshops(self):
        pass