from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

        cls.user_and_author = User.objects.create_user(username="test_author")
        cls.user_and_not_author = User.objects.create_user(username="test_not_author")

        cls.authorized_client_and_author = Client()
        cls.authorized_client_and_author.force_login(cls.user_and_author)

        cls.authorized_client_and_not_author = Client()
        cls.authorized_client_and_not_author.force_login(cls.user_and_not_author)

        cls.group = Group.objects.create(
            title="test_title",
            slug="test_slug",
            description="test_desc",
        )
        cls.post = Post.objects.create(
            text="test_text",
            author=cls.user_and_author,
            group=cls.group,
        )

        cls.INDEX_URL = "/"
        cls.POST_URL = f"/posts/{cls.post.id}/"
        cls.POST_EDIT_URL = f"/posts/{cls.post.id}/edit/"
        cls.GROUP_URL = f"/group/{cls.group.slug}/"
        cls.PROFILE_URL = f"/profile/{cls.user_and_author.username}/"
        cls.POST_CREATE_URL = "/create/"

        cls.ADD_COMMENT_URL = f"/posts/{cls.post.id}/comment/"

        cls.FOLLOW_INDEX_URL = "/follow/"
        cls.PROFILE_FOLLOW = f"/profile/{cls.user_and_author.username}/follow/"
        cls.PROFILE_UNFOLLOW = f"/profile/{cls.user_and_author.username}/unfollow/"

        cls.LOGIN_URL = "/auth/login/"

        cls.UNEXISTING_URL = "/unexisting/"

    def setUp(self):
        cache.clear()

    def test_accessible_pages(self):
        urlpatterns = (
            self.INDEX_URL,
            self.GROUP_URL,
            self.PROFILE_URL,
            self.POST_URL,
        )
        for url in urlpatterns:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create(self):
        response = self.authorized_client_and_author.get(self.POST_CREATE_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_redirect_for_guest_client(self):
        response = self.guest_client.get(self.POST_CREATE_URL, follow=True)
        self.assertRedirects(response, self.LOGIN_URL + "?next=" + self.POST_CREATE_URL)

    def test_post_edit_for_author(self):
        response = self.authorized_client_and_author.get(self.POST_EDIT_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_for_not_author(self):
        response = self.authorized_client_and_not_author.get(self.POST_EDIT_URL)
        self.assertRedirects(response, self.POST_URL)

    def test_post_edit_for_guest_client(self):
        response = self.guest_client.get(self.POST_EDIT_URL, follow=True)
        self.assertRedirects(response, self.LOGIN_URL + "?next=" + self.POST_EDIT_URL)

    def test_comment(self):
        response = self.authorized_client_and_author.get(self.ADD_COMMENT_URL)
        self.assertRedirects(response, self.POST_URL)

    def test_follow_index(self):
        response = self.authorized_client_and_author.get(self.FOLLOW_INDEX_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_follow_index_for_guest_client(self):
        response = self.guest_client.get(self.FOLLOW_INDEX_URL)
        self.assertRedirects(
            response, self.LOGIN_URL + "?next=" + self.FOLLOW_INDEX_URL
        )

    def test_profile_follow(self):
        response = self.authorized_client_and_author.get(self.PROFILE_FOLLOW)
        self.assertRedirects(response, self.PROFILE_URL)

    def test_profile_follow_for_guest_client(self):
        response = self.guest_client.get(self.PROFILE_FOLLOW)
        self.assertRedirects(response, self.LOGIN_URL + "?next=" + self.PROFILE_FOLLOW)

    def test_profile_unfollow(self):
        response = self.authorized_client_and_author.get(self.PROFILE_UNFOLLOW)
        self.assertRedirects(response, self.PROFILE_URL)

    def test_profile_unfollow_for_guest_client(self):
        response = self.guest_client.get(self.PROFILE_UNFOLLOW)
        self.assertRedirects(
            response, self.LOGIN_URL + "?next=" + self.PROFILE_UNFOLLOW
        )

    def error_404(self):
        response = self.guest_client.get("/unexisting/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            self.INDEX_URL: "posts/index.html",
            self.GROUP_URL: "posts/group_list.html",
            self.PROFILE_URL: "posts/profile.html",
            self.POST_URL: "posts/post_detail.html",
            self.POST_CREATE_URL: "posts/create_post.html",
            self.POST_EDIT_URL: "posts/create_post.html",
            self.UNEXISTING_URL: "core/404.html",
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_and_author.get(address)
                self.assertTemplateUsed(response, template)
