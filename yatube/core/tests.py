from django.test import Client, TestCase


class CoreTestClass(TestCase):
    def setUP(self):
        self.client = Client()

    def test_404_page_template(self):
        response = self.client.get('nonexist-page')
        self.assertTemplateUsed(response, 'core/404.html')
