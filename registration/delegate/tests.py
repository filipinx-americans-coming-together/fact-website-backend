from django.forms import model_to_dict
from django.test import Client, TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from registration.models import (
    Delegate,
    Location,
    NewSchool,
    Registration,
    School,
    Workshop,
)


class DelegatesPOST(TestCase):
    def setUp(self):
        self.client = Client()

        self.school = School.objects.create(name="School")

        location_1 = Location.objects.create(
            building="Building", room_num="ABC", session=1, capacity=10
        )
        location_2 = Location.objects.create(
            building="Building", room_num="12", session=2, capacity=10
        )
        location_3 = Location.objects.create(
            building="Another building", room_num="ABC", session=3, capacity=10
        )

        self.workshop_1 = Workshop.objects.create(
            title="title 1", description="description 1", location=location_1, session=1
        )
        self.workshop_2 = Workshop.objects.create(
            title="title 2", description="description 2", location=location_2, session=2
        )
        self.workshop_3 = Workshop.objects.create(
            title="title 3", description="description 3", location=location_3, session=3
        )

        self.good_data = {
            "f_name": "First",
            "l_name": "Second",
            "email": "email@email.com",
            "password": "pass-1243__?",
            "pronouns": "she/her",
            "year": "Junior",
            "school_id": self.school.pk,
            "workshop_1_id": self.workshop_1.pk,
            "workshop_2_id": self.workshop_2.pk,
            "workshop_3_id": self.workshop_3.pk,
        }

        self.url = reverse("registration:delegates")

    def test_email_already_exists(self):
        User.objects.create(username="anotheruser", email=self.good_data["email"])

        response = self.client.post(
            self.url, self.good_data, content_type="application/json"
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(User.objects.all().count(), 1)

    def test_missing_data(self):
        pass

    def test_bad_password(self):
        data = {
            "f_name": "First",
            "l_name": "Second",
            "email": "email@email.com",
            "password": "pass",
            "pronouns": "she/her",
            "year": "Junior",
            "school_id": self.school.pk,
            "workshop_1_id": self.workshop_1.pk,
            "workshop_2_id": self.workshop_2.pk,
            "workshop_3_id": self.workshop_3.pk,
        }

        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.all().count(), 0)

    def test_invalid_email(self):
        data = {
            "f_name": "First",
            "l_name": "Second",
            "email": "email",
            "password": "123j4klj+??",
            "pronouns": "she/her",
            "year": "Junior",
            "school_id": self.school.pk,
            "workshop_1_id": self.workshop_1.pk,
            "workshop_2_id": self.workshop_2.pk,
            "workshop_3_id": self.workshop_3.pk,
        }

        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.all().count(), 0)

    def test_full_workshops(self):
        # create other delegate to register for workshop
        location = Location.objects.create(
            building="new building", room_num="123", capacity=1, session=1
        )
        workshop = Workshop.objects.create(
            title="new workshop title",
            description="description",
            location=location,
            session=1,
        )
        user = User.objects.create(username="user123", email="email123@email.com")
        delegate = Delegate.objects.create(user=user, year="Senior", school=self.school)

        Registration.objects.create(workshop=workshop, delegate=delegate)

        data = {
            "f_name": "First",
            "l_name": "Second",
            "email": "email@email.com",
            "password": "123j4klj+??",
            "pronouns": "she/her",
            "year": "Junior",
            "school_id": self.school.pk,
            "workshop_1_id": workshop.pk,
            "workshop_2_id": self.workshop_2.pk,
            "workshop_3_id": self.workshop_3.pk,
        }

        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(User.objects.all().count(), 1)

    def test_same_session_workshops(self):
        data = {
            "f_name": "First",
            "l_name": "Second",
            "email": "email@email.com",
            "password": "123j4klj+??",
            "pronouns": "she/her",
            "year": "Junior",
            "school_id": self.school.pk,
            "workshop_1_id": self.workshop_2.pk,
            "workshop_2_id": self.workshop_2.pk,
            "workshop_3_id": self.workshop_3.pk,
        }

        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.all().count(), 0)

    def test_create_user_delegate_registration(self):
        response = self.client.post(
            self.url, self.good_data, content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.all().count(), 1)

        user = User.objects.get(
            first_name=self.good_data["f_name"],
            last_name=self.good_data["l_name"],
            username=self.good_data["email"],
            email=self.good_data["email"],
        )

        delegate = Delegate.objects.get(
            user=user,
            pronouns=self.good_data["pronouns"],
            year=self.good_data["year"],
            school_id=self.school.pk,
        )

        self.assertTrue(
            Registration.objects.filter(
                workshop_id=self.workshop_1.pk, delegate_id=delegate.pk
            ).exists()
        )
        self.assertTrue(
            Registration.objects.filter(
                workshop_id=self.workshop_2.pk, delegate_id=delegate.pk
            ).exists()
        )
        self.assertTrue(
            Registration.objects.filter(
                workshop_id=self.workshop_3.pk, delegate_id=delegate.pk
            ).exists()
        )

    def test_create_new_school(self):
        data = {
            "f_name": "First",
            "l_name": "Second",
            "email": "email@email.com",
            "password": "123j4klj+??",
            "pronouns": "she/her",
            "year": "Junior",
            "other_school_name": "some other school",
            "workshop_1_id": self.workshop_1.pk,
            "workshop_2_id": self.workshop_2.pk,
            "workshop_3_id": self.workshop_3.pk,
        }

        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.all().count(), 1)
        self.assertTrue(NewSchool.objects.filter(name="some other school").exists())


class DelegatesGET(TestCase):
    def setUp(self):
        pass

    def test_rejects_no_user(self):
        pass

    def test_rejects_non_delegate(self):
        pass

    def test_returns_delegate(self):
        pass


class DelegateLoginPOST(TestCase):
    def setUp(self):
        pass

    def test_rejects_invalid_creds(self):
        pass

    def test_rejects_non_delegate(self):
        pass

    def test_logs_in(self):
        pass


class UsersRequestPasswordResetPOST(TestCase):
    def setUp(self):
        pass

    def test_no_obj_created_if_no_user(self):
        pass

    def test_reject_no_email(self):
        pass

    def test_creates_reset_obj(self):
        pass


class UsersResetPasswordPOST(TestCase):
    def setUp(self):
        pass

    def test_reject_missing_email(self):
        pass

    def test_reject_missing_token(self):
        pass

    def test_reject_invalid_toke(self):
        pass

    def test_resets_password(self):
        pass


class UsersLogoutPOST(TestCase):
    def setUp(self):
        pass

    def test_logout(self):
        pass
