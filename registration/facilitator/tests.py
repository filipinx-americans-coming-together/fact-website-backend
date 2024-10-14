import json

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from registration.models import Facilitator


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
