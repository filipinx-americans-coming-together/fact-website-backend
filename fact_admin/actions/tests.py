import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group, User

from fact_admin.models import RegistrationFlag


class RegistrationFlagsGET(TestCase):
    def setUp(self):
        self.client = Client()

        self.expected_data = [
            {"label": "flag-1", "value": True},
            {"label": "flag-2", "value": True},
            {"label": "flag-3", "value": False},
            {"label": "flag-4", "value": True},
            {"label": "flag-5", "value": False},
        ]

        for flag in self.expected_data:
            RegistrationFlag.objects.create(label=flag["label"], value=flag["value"])

        self.url = reverse("fact_admin:flags")

    def test_gets_all_flags(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        data = response.json()

        actual = []
        for item in data:
            actual.append(
                {"label": item["fields"]["label"], "value": item["fields"]["value"]}
            )

        self.assertEqual(actual, self.expected_data)


class RegistrationFlagLabelGET(TestCase):
    def setUp(self):
        self.client = Client()

        RegistrationFlag.objects.create(label="first-flag", value=False)

        self.expected_label = "second-flag"
        self.expected_value = True

        self.flag = RegistrationFlag.objects.create(
            label=self.expected_label, value=self.expected_value
        )

        self.url_name = "fact_admin:flags_label"

    def test_flag_not_found(self):
        url = reverse(self.url_name, kwargs={"label": "not a label"})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_gets_flag(self):
        url = reverse(self.url_name, kwargs={"label": self.flag.label})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data[0]["fields"]["label"], self.flag.label)
        self.assertEqual(data[0]["fields"]["value"], self.flag.value)


class RegistrationFlagLabelPUT(TestCase):
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

        self.flag = RegistrationFlag.objects.create(label="some-label", value=False)

        self.good_data = {"value": True}

        self.url_name = "fact_admin:flags_label"

    def test_rejects_non_admin(self):
        response = self.client.put(
            reverse(self.url_name, kwargs={"label": self.flag.label}),
            json.dumps(self.good_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(RegistrationFlag.objects.get(pk=self.flag.pk).value, False)

        self.client.login(
            username=self.non_admin_username, password=self.non_admin_password
        )
        response = self.client.put(
            reverse(self.url_name, kwargs={"label": self.flag.label}),
            json.dumps(self.good_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(RegistrationFlag.objects.get(pk=self.flag.pk).value, False)

    def test_flag_not_found(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.put(
            reverse(self.url_name, kwargs={"label": "not a label"}),
            json.dumps(self.good_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)

    def test_invalid_value(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.put(
            reverse(self.url_name, kwargs={"label": self.flag.label}),
            json.dumps({"value": "example data"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(RegistrationFlag.objects.get(pk=self.flag.pk).value, False)

    def test_updates_flag(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.put(
            reverse(self.url_name, kwargs={"label": self.flag.label}),
            json.dumps(self.good_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            RegistrationFlag.objects.get(pk=self.flag.pk).value, self.good_data["value"]
        )


class SummaryGET(TestCase):
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

        self.url = reverse("fact_admin:summary")

    def test_rejects_non_admin(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

        self.client.login(
            username=self.non_admin_username, password=self.non_admin_password
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_gets_summary(self):
        self.client.login(username=self.username, password=self.password)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # TODO test actual data getting


class DelegateSheetGET(TestCase):
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

        self.url = reverse("fact_admin:delegate_sheet")

    def test_rejects_non_admin(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

        self.client.login(
            username=self.non_admin_username, password=self.non_admin_password
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    # TODO write test
    def test_gets_sheet(self):
        pass


class LocationSheetGET(TestCase):
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

        self.url = reverse("fact_admin:location_sheet")

    def test_rejects_non_admin(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

        self.client.login(
            username=self.non_admin_username, password=self.non_admin_password
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    # TODO write test
    def test_gets_sheet(self):
        pass
