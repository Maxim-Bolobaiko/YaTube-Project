import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsCreatePostTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

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
            name="small.gif",
            content=small_gif,
            content_type="image/gif",
        )

        cls.group = Group.objects.create(
            title="test_title",
            slug="test_slug",
            description="test_desc",
        )
        cls.post = Post.objects.create(
            text="Очень крутой текст очень крутого поста",
            author=cls.user,
            group=cls.group,
            image=cls.image,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_post(self):

        posts_count = Post.objects.count()

        form_data = {
            "text": self.post.text,
            "group": self.group.id,
            "image": self.post.image,
        }

        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                "posts:profile",
                kwargs={"username": self.user.username},
            ),
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.first()
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(self.post.image, "posts/small.gif")

    def test_edit_post(self):
        posts_count = Post.objects.count()
        form_data = {
            "text": self.post.text,
            "group": self.group.id,
        }
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": self.post.id}),
        )
        self.assertEqual(Post.objects.count(), posts_count)
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.author, self.post.author)

    def test_create_post_for_guest_client(self):
        posts_count = Post.objects.count()
        form_data = {
            "text": self.post.text,
            "group": self.group.id,
        }

        response = self.guest_client.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(
            response,
            reverse("users:login") + "?next=" + reverse("posts:post_create"),
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_comment(self):
        comments_count = Comment.objects.count()
        form_data = {"text": "Текст комментария"}

        response = self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data=form_data,
        )
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": self.post.id}),
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.text, form_data["text"])
        self.assertEqual(comment.author, self.user)

    def test_comment_for_guest_client(self):
        comments_count = Comment.objects.count()
        form_data = {"text": "Текст комментария"}

        response = self.guest_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data=form_data,
        )

        self.assertRedirects(
            response,
            reverse("users:login")
            + "?next="
            + reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
        )
        self.assertEqual(Comment.objects.count(), comments_count)
