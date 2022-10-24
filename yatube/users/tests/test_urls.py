from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class UsersURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()

        cls.user = User.objects.create_user(username="user")
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_accessible_pages(self):
        urlpatterns = (
            "/auth/signup/",
            "/auth/login/",
            "/auth/logout/",
        )
        for url in urlpatterns:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_password_change(self):
        response = self.authorized_client.get("/auth/password_change/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_password_change_redirect_for_guest_client(self):
        response = self.guest_client.get("/auth/password_change/", follow=True)
        self.assertRedirects(response, "/auth/login/?next=/auth/password_change/")

    def test_password_change_done(self):
        response = self.authorized_client.get("/auth/password_change/done/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_password_change_redirect_for_guest_client(self):
        response = self.guest_client.get("/auth/password_change/done/", follow=True)
        self.assertRedirects(response, "/auth/login/?next=/auth/password_change/done/")

    def error_404(self):
        response = self.guest_client.get("/unexisting/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        templates_urls_names = {
            "/auth/signup/": "users/signup.html",
            "/auth/login/": "users/login.html",
            "/auth/logout/": "users/logged_out.html",
        }
        for address, template in templates_urls_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
