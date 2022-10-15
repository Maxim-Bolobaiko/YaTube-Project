from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from users.forms import CreationForm

User = get_user_model()


class UsersViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username="user")
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.templates_pages_names = {
            reverse("users:login"): "users/login.html",
            reverse("users:logout"): "users/logged_out.html",
            reverse("users:signup"): "users/signup.html",
        }

    def test_pages_uses_correct_template(self):

        for (
            reverse_name,
            template_name,
        ) in UsersViewsTest.templates_pages_names.items():
            with self.subTest(uri=reverse_name, template_name=template_name):
                self.assertTemplateUsed(
                    self.authorized_client.get(reverse_name), template_name
                )

    def test_signup_show_correct_context(self):
        response = self.authorized_client.get(reverse("users:signup"))
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], CreationForm)
