from unittest import mock

from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse


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
