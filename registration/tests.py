from django.test import TestCase, Client
from django.urls import reverse

from .models import Workshop, Location, Facilitator, User
import json

class FacilitatorAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='facilitator1', email='facilitator1@example.com', password='password')
        self.facilitator = Facilitator.objects.create(user=self.user, fa_name="Facilitator One", fa_contact="123-456-7890")
        self.facilitator_url = reverse('registration:facilitator')

    def test_get_facilitator(self):
        self.client.login(username='facilitator1', password='password')
        
        response = self.client.get(self.facilitator_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Facilitator One")

    def test_post_facilitator(self):
        data = {
            "f_name": "New",
            "l_name": "Facilitator",
            "email": "newfacilitator@example.com",
            "password": "password123",
            "fa_name": "New Facilitator",
            "fa_contact": "987-654-3210",
            "workshops": []
        }
        response = self.client.post(self.facilitator_url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Facilitator.objects.count(), 2)  # 1 existing facilitator + 1 new facilitator

    def test_put_facilitator(self):
        self.client.login(username='facilitator1', password='password')
        
        data = {
            "f_name": "Updated",
            "l_name": "Facilitator",
            "email": "updatedfacilitator@example.com",
            "password": "newpassword123",
            "fa_name": "Updated Facilitator",
            "fa_contact": "111-222-3333",
            "workshops": []
        }
        response = self.client.put(self.facilitator_url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        
        self.facilitator.refresh_from_db()
        self.assertEqual(self.facilitator.fa_name, "Updated Facilitator")
        self.assertEqual(self.facilitator.fa_contact, "111-222-3333")

    def test_delete_facilitator(self):
        self.client.login(username='facilitator1', password='password')
        
        response = self.client.delete(self.facilitator_url)
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(Facilitator.DoesNotExist):
            Facilitator.objects.get(pk=self.facilitator.pk)

    def test_post_facilitator_already_exists(self):
        data = {
            "f_name": "Facilitator",
            "l_name": "One",
            "email": "facilitator1@example.com",
            "password": "password",
            "fa_name": "Facilitator One",
            "fa_contact": "123-456-7890",
            "workshops": []
        }
        response = self.client.post(self.facilitator_url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Email already in use", status_code=400)

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
            "location": self.location.id,
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

class LocationAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.location = Location.objects.create(
            room_num="101",
            building="Main Building",
            capacity=30
        )
        self.location_url = reverse('registration:location')
        self.location_id_url = reverse('registration:location_id', kwargs={'id': self.location.id})

    def test_post_location(self):
        data = {
            "room_num": "102",
            "building": "Annex Building",
            "capacity": 25
        }
        response = self.client.post(self.location_url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)

    def test_post_location_invalid_json(self):
        response = self.client.post(self.location_url, "Invalid JSON", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Invalid JSON", status_code=400)

    def test_post_location_already_exists(self):
        data = {
            "room_num": "101",
            "building": "Main Building",
            "capacity": 30
        }
        response = self.client.post(self.location_url, json.dumps(data), content_type="application/json")
        self.assertContains(response, "Location already exists", status_code=200)

    def test_get_location(self):
        response = self.client.get(self.location_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "101")

    def test_get_location_id(self):
        response = self.client.get(self.location_id_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "101")

    def test_put_location_id(self):
        data = {
            "room_num": "103",
            "building": "Main Building",
            "capacity": 40
        }
        response = self.client.put(self.location_id_url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.location.refresh_from_db()
        self.assertEqual(self.location.room_num, "103")

    def test_put_location_id_not_found(self):
        data = {
            "room_num": "104",
            "building": "Main Building",
            "capacity": 50
        }
        invalid_url = reverse('registration:location_id', kwargs={'id': 999})
        response = self.client.put(invalid_url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Location not found", status_code=404)

    def test_delete_location_id(self):
        response = self.client.delete(self.location_id_url)
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(Location.DoesNotExist):
            Location.objects.get(id=self.location.id)

    def test_delete_location_id_not_found(self):
        invalid_url = reverse('registration:location_id', kwargs={'id': 999})
        response = self.client.delete(invalid_url)
        self.assertEqual(response.status_code, 200)