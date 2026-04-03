import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from laundry.models import Basket
from wardrobe.models import CareAnalysis, Garment

User = get_user_model()


def _make_analysis(garment, image_hash):
    """Helper to create a CareAnalysis for a garment with standard test data."""
    return CareAnalysis.objects.create(
        garment=garment,
        image_hash=image_hash,
        raw_ai_json={},
        ai_washing='Machine wash cold (30°C)',
        ai_drying='Tumble dry low',
        ai_ironing='Low heat',
        ai_bleach='No bleach',
        ai_is_delicate=False,
        ai_summary='Normal wash',
        washing='Machine wash cold (30°C)',
        drying='Tumble dry low',
        ironing='Low heat',
        bleach='No bleach',
        is_delicate=False,
        summary='Normal wash',
    )


class BasketSelectionTest(TestCase):
    """Integration tests for BSKT-01: basket selection and persistence."""

    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='testpass123')
        self.client = Client(SERVER_NAME='localhost')
        self.client.login(email='test@example.com', password='testpass123')
        # Create garments — g1 and g2 have analysis, g3 does not
        self.g1 = Garment.objects.create(user=self.user, name='White Shirt', category='shirts', color='white')
        self.g2 = Garment.objects.create(user=self.user, name='Black Pants', category='bottoms', color='black')
        self.g3 = Garment.objects.create(user=self.user, name='No Analysis', category='shirts', color='red')
        _make_analysis(self.g1, 'aaa')
        _make_analysis(self.g2, 'bbb')

    def test_basket_page_loads(self):
        """GET /basket/ returns 200 for authenticated user."""
        response = self.client.get('/basket/')
        self.assertEqual(response.status_code, 200)

    def test_basket_page_requires_login(self):
        """GET /basket/ redirects unauthenticated user to login."""
        self.client.logout()
        response = self.client.get('/basket/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_only_analyzed_garments_in_context(self):
        """Basket view context contains only garments with analysis (BSKT-02)."""
        response = self.client.get('/basket/')
        garment_pks = [g.pk for g in response.context['garments']]
        self.assertIn(self.g1.pk, garment_pks)
        self.assertIn(self.g2.pk, garment_pks)
        self.assertNotIn(self.g3.pk, garment_pks)

    def test_basket_create(self):
        """POST /basket/create/ creates a new basket."""
        response = self.client.post('/basket/create/', {'name': 'Weekly Wash'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Basket.objects.filter(user=self.user, name='Weekly Wash').exists())

    def test_basket_create_max_5(self):
        """Cannot create more than 5 baskets."""
        for i in range(5):
            Basket.objects.create(user=self.user, name=f'Basket {i}')
        response = self.client.post('/basket/create/', {'name': 'Sixth'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Basket.objects.filter(user=self.user).count(), 5)

    def test_basket_delete(self):
        """POST /basket/<pk>/delete/ removes basket."""
        basket = Basket.objects.create(user=self.user, name='To Delete')
        response = self.client.post(f'/basket/{basket.pk}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Basket.objects.filter(pk=basket.pk).exists())

    def test_basket_rename(self):
        """POST /basket/<pk>/rename/ updates basket name."""
        basket = Basket.objects.create(user=self.user, name='Old Name')
        response = self.client.post(f'/basket/{basket.pk}/rename/', {'name': 'New Name'})
        self.assertEqual(response.status_code, 302)
        basket.refresh_from_db()
        self.assertEqual(basket.name, 'New Name')

    def test_update_selection(self):
        """POST /basket/update-selection/ persists garment_pks."""
        basket = Basket.objects.create(user=self.user, name='Test')
        response = self.client.post(
            '/basket/update-selection/',
            json.dumps({'basket_id': basket.pk, 'garment_pks': [self.g1.pk, self.g2.pk]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        basket.refresh_from_db()
        self.assertEqual(set(basket.garment_pks), {self.g1.pk, self.g2.pk})

    def test_cross_user_basket_404(self):
        """Other user's basket returns 404."""
        other = User.objects.create_user(email='other@example.com', password='testpass123')
        basket = Basket.objects.create(user=other, name='Not Mine')
        response = self.client.post(f'/basket/{basket.pk}/delete/')
        self.assertEqual(response.status_code, 404)


class PlanDisplayTest(TestCase):
    """Integration tests for BSKT-04: plan API and save."""

    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='testpass123')
        self.client = Client(SERVER_NAME='localhost')
        self.client.login(email='test@example.com', password='testpass123')
        self.g1 = Garment.objects.create(user=self.user, name='White Shirt', category='shirts', color='white')
        self.g2 = Garment.objects.create(user=self.user, name='Black Pants', category='bottoms', color='black')
        _make_analysis(self.g1, 'aaa')
        _make_analysis(self.g2, 'bbb')

    def test_plan_api_returns_loads(self):
        """POST /basket/api/plan/ returns JSON with loads key."""
        response = self.client.post(
            '/basket/api/plan/',
            json.dumps({'garment_pks': [self.g1.pk, self.g2.pk]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('loads', data)
        self.assertIn('special_care', data)

    def test_plan_api_min_2_garments(self):
        """Plan API rejects fewer than 2 garments."""
        response = self.client.post(
            '/basket/api/plan/',
            json.dumps({'garment_pks': [self.g1.pk]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_plan_api_max_20_garments(self):
        """Plan API rejects more than 20 garments."""
        response = self.client.post(
            '/basket/api/plan/',
            json.dumps({'garment_pks': list(range(1, 22))}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_plan_api_requires_login(self):
        """Plan API returns redirect for unauthenticated user."""
        self.client.logout()
        response = self.client.post(
            '/basket/api/plan/',
            json.dumps({'garment_pks': [self.g1.pk, self.g2.pk]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)

    def test_save_plan(self):
        """POST /basket/save-plan/ persists plan JSON."""
        basket = Basket.objects.create(user=self.user, name='Test')
        plan_data = {'loads': [{'color_group': 'whites', 'garments': []}], 'special_care': []}
        response = self.client.post(
            '/basket/save-plan/',
            json.dumps({'basket_id': basket.pk, 'plan': plan_data}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        basket.refresh_from_db()
        self.assertEqual(basket.saved_plan, plan_data)
        self.assertIsNotNone(basket.plan_saved_at)

    def test_saved_plan_in_context(self):
        """Basket with saved_plan passes plan data in context."""
        basket = Basket.objects.create(
            user=self.user,
            name='Test',
            saved_plan={'loads': [], 'special_care': []},
            plan_saved_at='2026-01-01T00:00:00Z',
        )
        response = self.client.get(f'/basket/?basket_id={basket.pk}')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['basket'].saved_plan)
