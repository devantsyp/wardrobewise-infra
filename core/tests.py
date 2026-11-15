from unittest import mock

from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse


class FaviconTests(TestCase):
    def test_favicon_ico_redirects_to_static_file(self):
        response = self.client.get('/favicon.ico')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('favicon.ico'))

    def test_pages_link_the_favicons(self):
        html = self.client.get(reverse('accounts:login')).content.decode()
        self.assertIn('favicon.svg', html)
        self.assertIn('apple-touch-icon.png', html)


class HealthzTests(TestCase):
    def test_returns_ok_when_database_reachable(self):
        response = self.client.get(reverse('core:healthz'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'database': 'ok'})

    def test_returns_503_when_database_unreachable(self):
        with mock.patch('core.views.connection.cursor', side_effect=OperationalError('db down')):
            with self.assertLogs('core.views', level='ERROR'):
                response = self.client.get(reverse('core:healthz'))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'status': 'error', 'database': 'unreachable'})
