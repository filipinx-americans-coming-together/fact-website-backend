import json
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.core import mail

from one_time_verification.models import PendingVerification


# Create your tests here.
class RequestPendingVerification(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("verifications:request")

    def test_reject_bad_data(self):
        # no email
        response = self.client.post(
            self.url,
            json.dumps({"email": "", "email_subject": "subject"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(PendingVerification.objects.all()), 0)

        response = self.client.post(
            self.url,
            json.dumps({"email_subject": "subject"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(PendingVerification.objects.all()), 0)

        # invalid email
        response = self.client.post(
            self.url,
            json.dumps({"email": "email", "email_subject": "subject"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(PendingVerification.objects.all()), 0)

        # no subject
        response = self.client.post(
            self.url,
            json.dumps({"email": "email@email.com", "email_subject": ""}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(PendingVerification.objects.all()), 0)

        response = self.client.post(
            self.url,
            json.dumps({"email": "email@email.com"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(PendingVerification.objects.all()), 0)

    def test_delete_existing(self):
        email = "test@test.com"

        old = PendingVerification.objects.create(
            email=email,
            code=123847,
            expiration=timezone.now() + timezone.timedelta(minutes=15),
        )

        response = self.client.post(
            self.url,
            json.dumps({"email": email, "email_subject": "testing"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(PendingVerification.objects.filter(email=email)), 1)
        self.assertNotEqual(PendingVerification.objects.get(email=email).code, old.code)

    def test_create_verification(self):
        email = "test@test.com"
        subject = "test"

        response = self.client.post(
            self.url,
            json.dumps({"email": email, "email_subject": subject}),
            content_type="application/json",
        )

        # create
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(PendingVerification.objects.filter(email=email)), 1)

        code = PendingVerification.objects.get(email=email).code

        # send email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(code, mail.outbox[0].body)


class VerifyPendingVerification(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("verifications:verify")

        self.email = "email@email.com"
        self.valid_code = 389024
        self.invalid_code = 489605

        self.valid_verification = PendingVerification.objects.create(
            email=self.email,
            code=self.valid_code,
            expiration=timezone.now() + timezone.timedelta(minutes=15),
        )

        self.expired_verification = PendingVerification.objects.create(
            email=self.email,
            code=self.invalid_code,
            expiration=timezone.now() - timezone.timedelta(minutes=15),
        )

    def test_reject_bad_data(self):
        # no email
        response = self.client.post(
            self.url,
            json.dumps({"email": "", "code": 489203}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(PendingVerification.objects.all()), 2)

        response = self.client.post(
            self.url,
            json.dumps({"code": 489203}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(PendingVerification.objects.all()), 2)

        # no code
        response = self.client.post(
            self.url,
            json.dumps({"email": self.email, "code": ""}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(PendingVerification.objects.all()), 2)

        response = self.client.post(
            self.url,
            json.dumps({"email": self.email}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(PendingVerification.objects.all()), 2)

    def test_reject_invalid_code(self):
        # expired
        response = self.client.post(
            self.url,
            json.dumps({"email": self.email, "code": self.invalid_code}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 409)
        # expired code should also be removed
        self.assertEqual(len(PendingVerification.objects.all()), 1)

        # does not exist
        response = self.client.post(
            self.url,
            json.dumps({"email": self.email, "code": self.valid_code + 1}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(len(PendingVerification.objects.all()), 1)

    def test_verified(self):
        response = self.client.post(
            self.url,
            json.dumps({"email": self.email, "code": self.valid_code}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(PendingVerification.objects.all()), 0)
