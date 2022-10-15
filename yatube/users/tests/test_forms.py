from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

        cls.users_count = User.objects.count()

        cls.new_user = {
            "username": "user",
            "first_name": "first name",
            "last_name": "last name",
            "email": "user@gmail.com",
            "password1": "some_crazy_password!!1",
            "password2": "some_crazy_password!!1",
        }

    def test_signup_create_new_user(self):

        response: HttpResponse = self.guest_client.post(
            reverse("users:signup"), data=self.new_user, follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(self.users_count + 1, User.objects.count())
