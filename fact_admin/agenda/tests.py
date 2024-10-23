import json
import random
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User, Group

from fact_admin.models import AgendaItem


class AgendaItems(TestCase):
    def setUp(self):
        self.client = Client()

        self.expected_items = []

        for i in range(10):
            start_time = timezone.now() + timezone.timedelta(
                hours=random.randint(0, 24)
            )

            new_item = AgendaItem.objects.create(
                title=f"item {i}",
                building="building",
                room_num=f"{i}",
                start_time=start_time,
                end_time=start_time + timezone.timedelta(hours=1),
            )

            self.expected_items.append((new_item.pk, start_time))

        self.expected_items = sorted(self.expected_items, key=lambda x: x[1])

    def test_gets_items_chronologically(self):
        response = self.client.get(reverse("fact_admin:agenda-items"))
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(AgendaItem.objects.all()), len(data))

        for i in range(len(self.expected_items)):
            expected_item = AgendaItem.objects.get(pk=self.expected_items[i][0])

            self.assertEqual(expected_item.title, data[i]["fields"]["title"])
            self.assertEqual(expected_item.building, data[i]["fields"]["building"])
            self.assertEqual(expected_item.room_num, data[i]["fields"]["room_num"])

            expected_start = expected_item.start_time.isoformat()[:-9] + "Z"
            self.assertEqual(expected_start, data[i]["fields"]["start_time"])

            expected_end = expected_item.end_time.isoformat()[:-9] + "Z"
            self.assertEqual(expected_end, data[i]["fields"]["end_time"])


class AgendaItemByID(TestCase):
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

        user = User(username=self.non_admin_password)
        user.set_password(self.non_admin_password)
        user.save()

        # data
        self.good_data = {
            "title": "example title",
            "start_time": "2024-10-18T00:02:17.590Z",
            "end_time": "2024-10-18T00:02:54.930Z",
            "building": "example building",
            "room_num": "example room",
            "session_num": 2,
        }

        self.url = reverse("fact_admin:agenda-items")

    def test_post_blocks_non_admin(self):
        response = self.client.post(
            self.url, json.dumps(self.good_data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(AgendaItem.objects.all()), 0)

        self.client.login(
            username=self.non_admin_username, password=self.non_admin_password
        )
        response = self.client.post(
            self.url, json.dumps(self.good_data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(AgendaItem.objects.all()), 0)

    def test_post_rejects_missing_data(self):
        self.client.login(username=self.username, password=self.password)

        missing_data = {
            "title": "",
            "start_time": "2024-10-18T00:02:17.590Z",
            "end_time": "2024-10-18T00:02:50.590Z",
            "building": "building",
            "room_num": "",
        }

        response = self.client.post(
            self.url, json.dumps(missing_data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(AgendaItem.objects.all()), 0)

        missing_data_2 = {
            "start_time": "2024-10-18T00:02:17.590Z",
            "end_time": "2024-10-18T00:02:40.590Z",
            "room_num": "123A",
        }

        response = self.client.post(
            self.url, json.dumps(missing_data_2), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(AgendaItem.objects.all()), 0)

    def test_post_rejects_invalid_times(self):
        self.client.login(username=self.username, password=self.password)

        invalid_times = {
            "title": "example title",
            "start_time": "2024-10-18T00:02:54.930Z",
            "end_time": "2024-10-18T00:02:17.590Z",
            "building": "example building",
            "room_num": "example room",
        }

        response = self.client.post(
            self.url, json.dumps(invalid_times), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(AgendaItem.objects.all()), 0)

    def test_post_rejects_invalid_session(self):
        self.client.login(username=self.username, password=self.password)

        invalid_session = {
            "title": "example title",
            "start_time": "2024-10-18T00:02:54.930Z",
            "end_time": "2024-10-18T00:02:17.590Z",
            "building": "example building",
            "room_num": "example room",
            "session_num": 4,
        }

        response = self.client.post(
            self.url, json.dumps(invalid_session), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(AgendaItem.objects.all()), 0)

    def test_post_creates_agenda_item(self):
        self.client.login(username=self.username, password=self.password)

        response = self.client.post(
            self.url, json.dumps(self.good_data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(AgendaItem.objects.all()), 1)

        data = response.json()[0]
        new_item = AgendaItem.objects.all()[0]

        self.assertEqual(data["pk"], new_item.pk)
        self.assertEqual(data["fields"]["title"], new_item.title)
        self.assertEqual(data["fields"]["building"], new_item.building)
        self.assertEqual(data["fields"]["room_num"], new_item.room_num)
        self.assertEqual(
            data["fields"]["start_time"], new_item.start_time.isoformat()[:-9] + "Z"
        )
        self.assertEqual(
            data["fields"]["end_time"], new_item.end_time.isoformat()[:-9] + "Z"
        )
        self.assertEqual(data["fields"]["session_num"], new_item.session_num)

    def test_delete_blocks_non_admin(self):
        # create item
        item = AgendaItem.objects.create(
            title="item title",
            building="building",
            room_num="room num",
            start_time="2024-10-18T00:02:17.590Z",
            end_time="2024-10-18T00:02:54.930Z",
        )

        response = self.client.delete(
            reverse("fact_admin:agenda-item", kwargs={"id": item.pk})
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(AgendaItem.objects.all()), 1)

        self.client.login(
            username=self.non_admin_username, password=self.non_admin_password
        )
        response = self.client.delete(
            reverse("fact_admin:agenda-item", kwargs={"id": item.pk})
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(AgendaItem.objects.all()), 1)

    def test_delete_404s_no_match(self):
        # create item
        item = AgendaItem.objects.create(
            title="item title",
            building="building",
            room_num="room num",
            start_time="2024-10-18T00:02:17.590Z",
            end_time="2024-10-18T00:02:54.930Z",
        )

        self.client.login(username=self.username, password=self.password)
        response = self.client.delete(
            reverse("fact_admin:agenda-item", kwargs={"id": item.pk + 1})
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(AgendaItem.objects.all()), 1)

    def tests_delete_deletes_item(self):
        # create item
        item = AgendaItem.objects.create(
            title="item title",
            building="building",
            room_num="room num",
            start_time="2024-10-18T00:02:17.590Z",
            end_time="2024-10-18T00:02:54.930Z",
        )

        self.client.login(username=self.username, password=self.password)
        response = self.client.delete(
            reverse("fact_admin:agenda-item", kwargs={"id": item.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(AgendaItem.objects.all()), 0)
