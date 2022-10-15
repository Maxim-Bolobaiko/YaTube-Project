from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class AboutURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()

        cls.user = User.objects.create_user(username="user")
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_accessible_pages(self):
        urlpatterns = (
            "/about/author/",
            "/about/tech/",
        )
        for url in urlpatterns:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        templates_urls_names = {
            "/about/author/": "about/author.html",
            "/about/tech/": "about/tech.html",
        }
        for address, template in templates_urls_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)


class AboutViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username="user")
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.templates_pages_names = {
            reverse("about:author"): "about/author.html",
            reverse("about:tech"): "about/tech.html",
        }

    def test_pages_uses_correct_template(self):

        for (
            reverse_name,
            template_name,
        ) in AboutViewsTest.templates_pages_names.items():
            with self.subTest(uri=reverse_name, template_name=template_name):
                self.assertTemplateUsed(
                    self.authorized_client.get(reverse_name), template_name
                )
