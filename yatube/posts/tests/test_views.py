import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username="author")
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )

        cls.image = SimpleUploadedFile(
            name="small_gif",
            content=small_gif,
            content_type="image/gif",
        )

        cls.group = Group.objects.create(
            title="test_title",
            slug="test_slug",
            description="test_desc",
        )
        cls.post = Post.objects.create(
            text="test_text",
            author=cls.user,
            group=cls.group,
            image=cls.image,
        )

        cls.templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", args=[cls.group.slug]
            ): "posts/group_list.html",
            reverse(
                "posts:profile", args=[cls.user.username]
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": cls.post.pk}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": cls.post.pk}
            ): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
        }

        cls.INDEX_URL = reverse("posts:index")
        cls.GROUP_URL = reverse(
            "posts:group_list", kwargs={"slug": cls.group.slug}
        )
        cls.PROFILE_URL = reverse(
            "posts:profile", kwargs={"username": cls.user.username}
        )
        cls.POST_EDIT_URL = reverse(
            "posts:post_edit", kwargs={"post_id": cls.post.pk}
        )
        cls.POST_CREATE_URL = reverse("posts:post_create")

        cls.form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()

    def test_pages_uses_correct_template(self):

        for (
            reverse_name,
            template,
        ) in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def _check_post_context(self, post):
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image, self.post.image)

    def test_index_group_list_and_profile_show_correct_context(self):
        urls = (
            self.INDEX_URL,
            self.GROUP_URL,
            self.PROFILE_URL,
        )
        for url in urls:
            with self.subTest():
                response = self.authorized_client.get(url)
                self._check_post_context(
                    response.context.get("page_obj").object_list[0]
                )

    def test_post_detail_show_correct_context(self):
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.pk})
        )
        self._check_post_context(response.context.get("post"))

    def test_post_edit_and_post_create_show_correct_context(self):
        urls = {
            self.POST_CREATE_URL,
            self.POST_EDIT_URL,
        }
        for url in urls:
            with self.subTest():
                response = self.authorized_client.get(url)
                for value, expected in self.form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context["form"].fields[value]
                        self.assertIsInstance(form_field, expected)

    def test_index_group_list_profile_add_post(self):
        new_post = Post.objects.create(
            text="test_text",
            author=self.user,
            group=self.group,
        )

        names_url = {
            "index": self.INDEX_URL,
            "group_list": self.GROUP_URL,
            "profile": self.PROFILE_URL,
        }

        for name, url in names_url.items():
            with self.subTest(name=name):
                response = self.authorized_client.get(url)
                self.assertEqual(response.context["page_obj"][0], new_post)

    def test_post_in_correct_group(self):
        other_group = Group.objects.create(
            title="other_group",
            slug="other_slug",
            description="other_desc",
        )
        response = self.authorized_client.get(
            reverse("posts:group_list", kwargs={"slug": other_group.slug})
        )
        context_object = response.context["page_obj"].object_list
        self.assertNotIn(self.post, context_object)


class PostsPaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="author")
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title="test_title",
            slug="test_slug",
            description="test_desc",
        )

        cls.POSTS_COUNT = 12

        cls.posts = []
        for i in range(cls.POSTS_COUNT):
            cls.posts.append(
                Post(author=cls.user, group=cls.group, text="test_text")
            )
        cls.post = Post.objects.bulk_create(cls.posts)

        cls.INDEX_URL = reverse("posts:index")
        cls.GROUP_URL = reverse(
            "posts:group_list", kwargs={"slug": cls.group.slug}
        )
        cls.PROFILE_URL = reverse(
            "posts:profile", kwargs={"username": cls.user.username}
        )

    def test_first_page_10(self):
        urls = {
            "index": self.INDEX_URL,
            "group_list": self.GROUP_URL,
            "profile": self.PROFILE_URL,
        }
        for name, url in urls.items():
            with self.subTest(name=name):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    len(response.context.get("page_obj").object_list),
                    settings.PAGE_NUMBER_CONST,
                )

    def test_second_page_posts(self):
        names_urls = {
            "index": self.INDEX_URL + "?page=2",
            "group_list": self.GROUP_URL + "?page=2",
            "profile": self.PROFILE_URL + "?page=2",
        }

        posts_on_n_page = Post.objects.count() % settings.PAGE_NUMBER_CONST

        for name, url in names_urls.items():
            with self.subTest(name=name):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    len(response.context.get("page_obj").object_list),
                    posts_on_n_page,
                )


class PostCacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username="user")
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.post = Post.objects.create(
            text="test_text",
            author=cls.user,
        )

    def test_cache(self):
        response = self.authorized_client.get(reverse("posts:index"))

        self.post.delete()

        response_after_delete = self.client.get(reverse("posts:index"))
        self.assertEqual(response.content, response_after_delete.content)

        cache.clear()

        response_after_cache_clear = self.client.get(reverse("posts:index"))
        self.assertNotEqual(
            response_after_delete.content, response_after_cache_clear.content
        )


class PostFollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user_follower = User.objects.create_user(username="user_follower")
        cls.user_following = User.objects.create_user(
            username="user_following"
        )
        cls.user_random = User.objects.create_user(username="user_random")

        cls.authorized_client_follower = Client()
        cls.authorized_client_following = Client()
        cls.authorized_client_random = Client()

        cls.authorized_client_follower.force_login(cls.user_follower)
        cls.authorized_client_following.force_login(cls.user_following)
        cls.authorized_client_random.force_login(cls.user_random)

        cls.post = Post.objects.create(
            text="test_text",
            author=cls.user_following,
        )

    def test_follow(self):
        follow_count = Follow.objects.count()
        self.authorized_client_follower.get(
            reverse(
                "posts:profile_follow", args=(self.user_following.username,)
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user_following,
            )
        )

    def test_unfollow(self):
        follow_count = Follow.objects.count()
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following,
        )
        self.authorized_client_follower.get(
            reverse(
                "posts:profile_unfollow", args=(self.user_following.username,)
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user_following,
            )
        )

    def test_new_post_in_followers_feed(self):
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following,
        )
        post = Post.objects.create(
            author=self.user_following, text="test_text"
        )

        response = self.authorized_client_follower.get(
            reverse("posts:follow_index")
        )

        self.assertIn(post, response.context["page_obj"])

    def test_new_post_not_in_randoms_feed(self):
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following,
        )
        post = Post.objects.create(
            author=self.user_following, text="test_text"
        )

        response = self.authorized_client_random.get(
            reverse("posts:follow_index")
        )

        self.assertNotIn(post, response.context["page_obj"])
