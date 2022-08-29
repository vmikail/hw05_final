import shutil
import tempfile
from datetime import date

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Group, Post, Comment
from ..forms import PostForm


User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            pub_date=date.today(),
            group=cls.group,
        )
        cls.form = PostForm()

    def setUp(self):
        cache.clear()
        self.guest = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_auth_client(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        count_posts = Post.objects.count() + 1
        form_data = {
            'text': 'Дополнительный Тестовый пост',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), count_posts)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': f'{self.post.author}'}
        ))
        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                text='Дополнительный Тестовый пост',
                group=self.group.id,
                image='posts/small.gif'
            ).exists()
        )

    def test_post_edit(self):
        group = Group.objects.create(
            title="Тестовая группа 2",
            description="Test2",
            slug="test-slug2",
        )
        Post.objects.create(
            text="Text",
            author=self.user
        )
        posts_count = Post.objects.count()
        form_data = {
            "group": group.id,
            "text": "редактированный текст",
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 2}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            "posts:post_detail",
            kwargs={"post_id": 2}
        ))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(
            Post.objects.first().text,
            "редактированный текст"
        )
        self.assertEqual(
            Post.objects.first().group.title,
            "Тестовая группа 2"
        )
        self.assertEqual(
            Post.objects.first().pk,
            2
        )

    def test_comment_only_authorised(self):
        """Проверка: комментирует может только авторизованный пользователь"""
        response = self.guest.get(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id}
        ))
        response_auth = self.authorized_client.get(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id}
        ))
        redirect_url = f'/auth/login/?next=/posts/{self.post.id}/comment/'
        redirect_post_detail = f'/posts/{self.post.id}/'
        self.assertRedirects(response, redirect_url)
        self.assertRedirects(response_auth, redirect_post_detail)

    def test_comment_on_post_details(self):
        """Тест на отправку комментария"""
        count_comments = Comment.objects.count()
        form_data = {'text': 'Это комментарий'}
        response = self.authorized_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id}
        ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ))
        self.assertEqual(Comment.objects.count(), count_comments + 1)
        self.assertTrue(Comment.objects.filter(
            text=form_data['text']
        ).exists())
