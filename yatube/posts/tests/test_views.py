import shutil
import tempfile
import time

from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Group, Post
from ..forms import PostForm


User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        posts = [
            Post(
                author=cls.user,
                text=f'{i} Тестовый пост',
                group=cls.group2,
            ) for i in range(12, 0, -1)
        ]
        Post.objects.bulk_create(posts)
        time.sleep(1E-6)
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост c картинкой',
            group=cls.group,
            image=uploaded
        )
        cls.count_of_posts = (Post.objects.filter(
            author=cls.user).count())

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_post = Client()
        self.author_post.force_login(self.post.author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_templates(self):
        """Проверка namespace:name"""
        templates_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': f'{self.group.slug}'}
            ):
            'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}):
            'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ):
            'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        for reverse_name, template in templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_post.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_paginator_first_page(self):
        """Проверка пагинатора первой страницы index """
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_index_paginator_second_page(self):
        """Проверка пагинатора второй страницы index """
        response = self.guest_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_group_paginator_first_page(self):
        """Проверка пагинатора первой страницы group posts """
        response = self.guest_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': f'{self.group2.slug}'})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_paginator_second_page(self):
        """Проверка пагинатора второй страницы group posts """
        response = self.guest_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': f'{self.group2.slug}'}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_profile_paginator_first_page(self):
        """Проверка пагинатора первой страницы profile """
        response = self.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.post.author}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_paginator_second_page(self):
        """Проверка пагинатора второй страницы profile """
        response = self.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.post.author}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)

    def check_context_page(self, context):
        self.assertIn('page_obj', context)
        post = context['page_obj'][0]
        self.assertEqual(post.author, PostViewsTest.user)
        self.assertEqual(post.pub_date, PostViewsTest.post.pub_date)
        self.assertEqual(post.text, PostViewsTest.post.text)
        self.assertEqual(post.group, PostViewsTest.post.group)
        self.assertEqual(post.image, PostViewsTest.post.image)
        self.assertIn('title', context)

    def test_index_context_is_correct(self):
        """Проверка index context"""
        response = self.guest_client.get(reverse('posts:index'))
        self.check_context_page(context=response.context)

    def test_group_context_is_correct(self):
        """Проверка group posts context"""
        response = self.guest_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': f'{self.group.slug}'}
        ))
        self.check_context_page(context=response.context)
        self.assertEqual(str(response.context['group']), 'Тестовая группа')

    def test_profile_context_is_correct(self):
        """Проверка profile context"""
        response = self.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.post.author}
        ))
        self.check_context_page(context=response.context)
        self.assertEqual(
            str(response.context['user']),
            str(PostViewsTest.user)
        )
        self.assertEqual(
            str(response.context['author']),
            str(PostViewsTest.user)
        )

    def test_post_detail_context_is_correct(self):
        """Проверка post_detail"""
        response = self.guest_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ))
        get_post = response.context.get('post')
        self.assertEqual(
            get_post.text,
            PostViewsTest.post.text
        )
        self.assertEqual(
            get_post.pub_date,
            PostViewsTest.post.pub_date
        )
        self.assertEqual(
            get_post.author,
            PostViewsTest.post.author
        )
        self.assertEqual(
            get_post.group,
            PostViewsTest.post.group
        )
        self.assertEqual(
            response.context.get('posts_count'),
            PostViewsTest.count_of_posts
        )
        self.assertEqual(
            get_post.image,
            PostViewsTest.post.image
        )

    def test_post_create_context(self):
        """Проверка контекста в post_create"""
        response = self.author_post.get(reverse(
            'posts:post_create'
        ))
        form_obj = response.context.get('form')
        form_edit = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for field, expected_type in form_edit.items():
            with self.subTest(field=field):
                field_type = form_obj.fields.get(field)
                self.assertIsInstance(field_type, expected_type)
        self.assertIsInstance(form_obj, PostForm)
        self.assertNotIn('is_edit', response.context)

    def test_post_edit_context(self):
        """Проверка контекста в post_edit"""
        response = self.author_post.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id}
        ))
        form_obj = response.context.get('form')
        form_edit = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for field, expected_type in form_edit.items():
            with self.subTest(field=field):
                field_type = form_obj.fields.get(field)
                self.assertIsInstance(field_type, expected_type)
        self.assertIsInstance(form_obj, PostForm)

    def test_index_cache(self):
        Post.objects.create(
            author=self.user,
            text='test',
        )
        post_count = Post.objects.count()
        response = self.guest_client.get('/')
        cached_response_content = response.content
        Post.objects.first().delete()
        self.assertEqual(Post.objects.count(), post_count - 1)
        self.assertEqual(cached_response_content, response.content)
        cache.clear()
        response1 = self.guest_client.get('/')
        self.assertNotEqual(cached_response_content, response1.content)
