from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from http import HTTPStatus

User = get_user_model()


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='noname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url(self):
        url_template = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }

        for adress, template in url_template.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_404_url(self):
        response_url = {
            self.guest_client: '/unexisting_page/',
            self.authorized_client: '/unexisting_page/',
        }
        for client, url in response_url.items():
            with self.subTest(client=client):
                response = client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
