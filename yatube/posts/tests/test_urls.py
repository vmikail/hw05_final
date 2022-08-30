from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache

from ..models import Group, Post, Comment


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='guest')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_post = Client()
        self.author_post.force_login(self.post.author)

    def test_pages_all(self):
        post_id = f'/posts/{self.post.id}/'
        url_status = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.post.author}/': HTTPStatus.OK,
            post_id: HTTPStatus.OK,
            'unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for address, status in url_status.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_pages_registred(self):
        post_id = f'/posts/{self.post.id}/'
        url_status = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user}/': HTTPStatus.OK,
            post_id: HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            '/create/': HTTPStatus.OK,
        }
        for address, status in url_status.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_edit_page_for_author(self):
        edit_post = f'/posts/{self.post.id}/edit/'
        with self.subTest(address=edit_post):
            response = self.author_post.get(edit_post)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_page_for_authorized_non_author(self):
        edit_post = f'/posts/{self.post.id}/edit/'
        response = self.authorized_client.get(edit_post)
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_edit_and_create_page_for_guest(self):
        edit_redir = f'/auth/login/?next=/posts/{self.post.id}/edit/'
        url_redir = {
            f'/posts/{self.post.id}/edit/': edit_redir,
            '/create/': '/auth/login/?next=/create/',
        }
        for address, redir in url_redir.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redir)
