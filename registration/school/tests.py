import json
import io
import pandas as pd
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from registration.models import School, NewSchool, Delegate

class SchoolViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(username='admin', password='password')
        self.admin_group = Group.objects.create(name='FACTAdmin')
        self.admin_user.groups.add(self.admin_group)
        self.regular_user = User.objects.create_user(username='user', password='password')
        self.school = School.objects.create(name='Test School')
        self.new_school = NewSchool.objects.create(name='New School')
        self.schools_url = reverse('registration:schools')
        self.new_schools_url = reverse('registration:schools_new')
        self.schools_bulk_url = reverse('registration:schools_bulk')

    def test_schools_get(self):
        response = self.client.get(self.schools_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test School', response.content.decode())

    def test_schools_method_not_allowed(self):
        response = self.client.post(self.schools_url)
        self.assertEqual(response.status_code, 405)
        self.assertIn('Method not allowed', response.json().get('message', ''))

    def test_new_schools_get(self):
        response = self.client.get(self.new_schools_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('New School', response.content.decode())

    def test_new_schools_post_admin_success(self):
        self.client.force_login(self.admin_user)
        Delegate.objects.create(user=self.regular_user, other_school='New School')
        data = {"other_school": "New School", "approved_name": "Approved School"}
        response = self.client.post(self.new_schools_url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json().get('message', ''))
        self.assertTrue(School.objects.filter(name='Approved School').exists())
        self.assertFalse(NewSchool.objects.filter(name='New School').exists())
        delegate = Delegate.objects.get(user=self.regular_user)
        self.assertEqual(delegate.school.name, 'Approved School')
        self.assertIsNone(delegate.other_school)

    def test_new_schools_post_non_admin(self):
        self.client.force_login(self.regular_user)
        data = {"other_school": "New School", "approved_name": "Approved School"}
        response = self.client.post(self.new_schools_url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertIn('Must be admin', response.json().get('message', ''))

    def test_new_schools_post_missing_approved_name(self):
        self.client.force_login(self.admin_user)
        data = {"other_school": "New School"}
        response = self.client.post(self.new_schools_url, json.dumps(data), content_type="application/json")
        self.assertIn('Must provide approved name', response.json().get('message', ''))

    def test_new_schools_method_not_allowed(self):
        response = self.client.put(self.new_schools_url)
        self.assertEqual(response.status_code, 405)
        self.assertIn('Method not allowed', response.json().get('message', ''))

    def test_schools_bulk_post_admin_success(self):
        self.client.force_login(self.admin_user)
        School.objects.all().delete()
        df = pd.DataFrame({"name": ["Bulk School 1", "Bulk School 2"]})
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        response = self.client.post(self.schools_bulk_url, {"schools": excel_file}, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(School.objects.filter(name="Bulk School 1").exists())
        self.assertTrue(School.objects.filter(name="Bulk School 2").exists())

    def test_schools_bulk_post_non_admin(self):
        self.client.force_login(self.regular_user)
        response = self.client.post(self.schools_bulk_url)
        self.assertEqual(response.status_code, 403)
        self.assertIn('Must be admin', response.json().get('message', ''))

    def test_schools_bulk_post_existing_schools(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(self.schools_bulk_url)
        self.assertEqual(response.status_code, 409)
        self.assertIn('Delete existing schools', response.json().get('message', ''))

    def test_schools_bulk_post_missing_file(self):
        self.client.force_login(self.admin_user)
        School.objects.all().delete()
        response = self.client.post(self.schools_bulk_url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Must include file', response.json().get('message', ''))

    def test_schools_bulk_post_duplicate_columns(self):
        self.client.force_login(self.admin_user)
        School.objects.all().delete()
        df = pd.DataFrame({"name": ["School 1"], "name.1": ["School 2"]})
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        response = self.client.post(self.schools_bulk_url, {"schools": excel_file}, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Duplicate column names', response.json().get('message', ''))

    def test_schools_bulk_post_missing_values(self):
        self.client.force_login(self.admin_user)
        School.objects.all().delete()
        df = pd.DataFrame({"name": [None]})
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        response = self.client.post(self.schools_bulk_url, {"schools": excel_file}, format='multipart')
        self.assertEqual(response.status_code, 200)

    def test_schools_bulk_method_not_allowed(self):
        response = self.client.get(self.schools_bulk_url)
        self.assertEqual(response.status_code, 405)
        self.assertIn('Method not allowed', response.json().get('message', ''))
