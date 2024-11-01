from datetime import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware
from django.contrib.auth.models import User, Group

from fact_admin.models import Notification


class NotificationsGET(TestCase):
    def setUp(self):
        self.client = Client()

        self.expected = []

        for i in range(4):
            notification = Notification.objects.create(
                message=f"message {i}",
                expiration=timezone.now() + timezone.timedelta(days=1 + i),
            )

            self.expected.append(notification.message)

        Notification.objects.create(
            message="message", expiration=timezone.now() - timezone.timedelta(days=1)
        )

        self.url = reverse("fact_admin:notifications")

    def test_gets_not_expired(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        data = response.json()
        expected = []

        for item in data:
            expected.append(item["fields"]["message"])

        self.assertEqual(len(data), len(self.expected))
        self.assertListEqual(expected, self.expected)


class NotificationsPOST(TestCase):
    def setUp(self):
        self.client = Client()

        # users
        group = Group.objects.create(name="FACTAdmin")

        self.username = "admin-user"
        self.password = "admin-pass"

        user = User(username=self.username)
        user.set_password(self.password)
        user.save()

        user.groups.add(group)

        self.non_admin_username = "non-admin-user"
        self.non_admin_password = "non-admin-pass"

        user = User(username=self.non_admin_username)
        user.set_password(self.non_admin_password)
        user.save()

        self.good_data = {
            "message": "notification message",
            "expiration": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
        }

        self.url = reverse("fact_admin:notifications")

    def test_rejects_non_admin(self):
        response = self.client.post(
            self.url, self.good_data, content_type="application/json"
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Notification.objects.all().count(), 0)

        self.client.login(
            username=self.non_admin_username, password=self.non_admin_password
        )
        response = self.client.post(
            self.url, self.good_data, content_type="application/json"
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Notification.objects.all().count(), 0)

    def test_missing_data(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(
            self.url, {"message": ""}, content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Notification.objects.all().count(), 0)

    def test_duplicate_messages(self):
        message = "my message"

        Notification.objects.create(
            message=message, expiration=timezone.now() + timezone.timedelta(days=1)
        )

        self.client.login(username=self.username, password=self.password)
        response = self.client.post(
            self.url,
            {
                "message": message,
                "expiration": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(Notification.objects.all().count(), 1)

    def test_create_notification(self):
        Notification.objects.create(
            message="message", expiration=timezone.now() - timezone.timedelta(days=1)
        )

        self.client.login(username=self.username, password=self.password)
        response = self.client.post(
            self.url,
            self.good_data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        # should also delete stale notifs
        self.assertEqual(Notification.objects.all().count(), 1)

        created_notif = Notification.objects.get(message=self.good_data["message"])
        self.assertEqual(
            created_notif.expiration,
            datetime.fromisoformat(self.good_data["expiration"]),
        )


class NotificationsDELETE(TestCase):
    def setUp(self):
        self.client = Client()

        # users
        group = Group.objects.create(name="FACTAdmin")

        self.username = "admin-user"
        self.password = "admin-pass"

        user = User(username=self.username)
        user.set_password(self.password)
        user.save()

        user.groups.add(group)

        self.non_admin_username = "non-admin-user"
        self.non_admin_password = "non-admin-pass"

        user = User(username=self.non_admin_username)
        user.set_password(self.non_admin_password)
        user.save()

        self.notif_id = Notification.objects.create(
            message="message", expiration=timezone.now() + timezone.timedelta(days=1)
        ).pk

        self.url_name = "fact_admin:notifications_id"

    def test_rejects_non_admin(self):
        response = self.client.delete(
            reverse(self.url_name, kwargs={"id": self.notif_id}),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Notification.objects.all().count(), 1)

        self.client.login(
            username=self.non_admin_username, password=self.non_admin_password
        )
        response = self.client.delete(
            reverse(self.url_name, kwargs={"id": self.notif_id}),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Notification.objects.all().count(), 1)

    def test_notification_not_found(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.delete(
            reverse(self.url_name, kwargs={"id": self.notif_id + 1}),
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Notification.objects.all().count(), 1)

    def test_deletes_notification(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.delete(
            reverse(self.url_name, kwargs={"id": self.notif_id}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.all().count(), 0)
