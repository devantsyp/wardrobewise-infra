"""
Unit tests for group_into_loads() grouping algorithm.

All tests use plain dicts as input — no ORM or database needed.
"""

from django.test import SimpleTestCase

from laundry.services.grouping import group_into_loads


def make_garment(
    pk=1,
    name='Test',
    color='white',
    washing='Machine wash cold (30°C)',
    drying='Tumble dry low',
    bleach='Non-chlorine bleach only',
    is_delicate=False,
    photo_url=None,
    category='shirts',
):
    return {
        'pk': pk,
        'name': name,
        'photo_url': photo_url,
        'category': category,
        'color': color,
        'washing': washing,
        'drying': drying,
        'bleach': bleach,
        'is_delicate': is_delicate,
    }


class GroupingLogicTest(SimpleTestCase):

    # -------------------------------------------------------------------------
    # Empty / trivial cases
    # -------------------------------------------------------------------------

    def test_empty_list_returns_empty(self):
        result = group_into_loads([])
        self.assertEqual(result, {'loads': [], 'special_care': []})

    # -------------------------------------------------------------------------
    # Special care routing
    # -------------------------------------------------------------------------

    def test_dry_clean_only_routed_to_special_care(self):
        g = make_garment(pk=1, washing='Dry clean only')
        result = group_into_loads([g])
        self.assertEqual(result['loads'], [])
        self.assertEqual(len(result['special_care']), 1)
        item = result['special_care'][0]
        self.assertEqual(item['pk'], 1)
        self.assertIn('dry clean', item['care_method'].lower())

    def test_hand_wash_only_routed_to_special_care(self):
        g = make_garment(pk=2, washing='Hand wash only')
        result = group_into_loads([g])
        self.assertEqual(result['loads'], [])
        self.assertEqual(len(result['special_care']), 1)
        self.assertIn('hand wash', result['special_care'][0]['care_method'].lower())

    def test_do_not_wash_routed_to_special_care(self):
        g = make_garment(pk=3, washing='Do not wash')
        result = group_into_loads([g])
        self.assertEqual(result['loads'], [])
        self.assertEqual(len(result['special_care']), 1)

    def test_all_special_care_returns_empty_loads(self):
        garments = [
            make_garment(pk=1, washing='Dry clean only'),
            make_garment(pk=2, washing='Dry clean only'),
            make_garment(pk=3, washing='Hand wash only'),
        ]
        result = group_into_loads(garments)
        self.assertEqual(result['loads'], [])
        self.assertEqual(len(result['special_care']), 3)

    # -------------------------------------------------------------------------
    # Color classification
    # -------------------------------------------------------------------------

    def test_whites_classification(self):
        for color in ['white', 'cream', 'ivory']:
            g = make_garment(color=color)
            result = group_into_loads([g])
            self.assertEqual(len(result['loads']), 1, f"Expected 1 load for color={color}")
            self.assertEqual(result['loads'][0]['color_group'], 'whites', f"Failed for color={color}")

    def test_darks_classification(self):
        for color in ['black', 'navy', 'charcoal']:
            g = make_garment(color=color)
            result = group_into_loads([g])
            self.assertEqual(len(result['loads']), 1, f"Expected 1 load for color={color}")
            self.assertEqual(result['loads'][0]['color_group'], 'darks', f"Failed for color={color}")

    def test_lights_classification(self):
        for color in ['blue', 'pink', '']:
            g = make_garment(color=color)
            result = group_into_loads([g])
            self.assertEqual(len(result['loads']), 1, f"Expected 1 load for color={color}")
            self.assertEqual(result['loads'][0]['color_group'], 'lights', f"Failed for color={color}")

    def test_color_case_insensitive(self):
        g_black = make_garment(pk=1, color='BLACK')
        result = group_into_loads([g_black])
        self.assertEqual(result['loads'][0]['color_group'], 'darks')

        g_white = make_garment(pk=2, color='White')
        result = group_into_loads([g_white])
        self.assertEqual(result['loads'][0]['color_group'], 'whites')

    # -------------------------------------------------------------------------
    # Temperature extraction
    # -------------------------------------------------------------------------

    def test_temperature_extraction_celsius(self):
        g = make_garment(washing='Machine wash cold (30°C)')
        result = group_into_loads([g])
        self.assertEqual(result['loads'][0]['temperature'], 30)

    def test_temperature_extraction_degrees(self):
        g = make_garment(washing='Wash at 40 degrees C')
        result = group_into_loads([g])
        self.assertEqual(result['loads'][0]['temperature'], 40)

    def test_temperature_keyword_cold(self):
        g = make_garment(washing='Cold wash only')
        result = group_into_loads([g])
        self.assertEqual(result['loads'][0]['temperature'], 30)

    def test_temperature_keyword_warm(self):
        g = make_garment(washing='Wash in warm water')
        result = group_into_loads([g])
        self.assertEqual(result['loads'][0]['temperature'], 40)

    def test_temperature_keyword_hot(self):
        g = make_garment(washing='Hot wash')
        result = group_into_loads([g])
        self.assertEqual(result['loads'][0]['temperature'], 60)

    def test_temperature_null_defaults_to_30(self):
        g = make_garment(washing='Unable to determine')
        result = group_into_loads([g])
        load = result['loads'][0]
        self.assertEqual(load['temperature'], 30)
        self.assertEqual(load['temp_label'], 'Coolest wash')

    def test_temperature_empty_string(self):
        g = make_garment(washing='')
        result = group_into_loads([g])
        load = result['loads'][0]
        self.assertEqual(load['temperature'], 30)
        self.assertEqual(load['temp_label'], 'Coolest wash')

    # -------------------------------------------------------------------------
    # Delicates separation
    # -------------------------------------------------------------------------

    def test_delicates_separated_when_mixed(self):
        g1 = make_garment(pk=1, color='blue', washing='Machine wash cold (30°C)', is_delicate=True)
        g2 = make_garment(pk=2, color='blue', washing='Machine wash cold (30°C)', is_delicate=False)
        result = group_into_loads([g1, g2])
        self.assertEqual(len(result['loads']), 2)
        cycles = {load['cycle'] for load in result['loads']}
        self.assertIn('delicate', cycles)
        self.assertIn('normal', cycles)

    def test_delicates_not_separated_when_all_delicate(self):
        g1 = make_garment(pk=1, color='blue', washing='Machine wash cold (30°C)', is_delicate=True)
        g2 = make_garment(pk=2, color='blue', washing='Machine wash cold (30°C)', is_delicate=True)
        result = group_into_loads([g1, g2])
        self.assertEqual(len(result['loads']), 1)
        self.assertEqual(result['loads'][0]['cycle'], 'delicate')

    # -------------------------------------------------------------------------
    # Warning extraction
    # -------------------------------------------------------------------------

    def test_warning_air_dry(self):
        g = make_garment(drying='Air dry only')
        result = group_into_loads([g])
        garment_warnings = result['loads'][0]['garments'][0]['warnings']
        self.assertIn('air dry only', garment_warnings)

    def test_warning_no_bleach(self):
        g = make_garment(bleach='Do not bleach')
        result = group_into_loads([g])
        garment_warnings = result['loads'][0]['garments'][0]['warnings']
        self.assertIn('no bleach', garment_warnings)

    def test_warning_no_tumble_dry(self):
        g = make_garment(drying='Do not tumble dry')
        result = group_into_loads([g])
        garment_warnings = result['loads'][0]['garments'][0]['warnings']
        self.assertIn('no tumble dry', garment_warnings)

    def test_warning_delicate_cycle(self):
        g = make_garment(washing='Delicate cycle, 30°C')
        result = group_into_loads([g])
        garment_warnings = result['loads'][0]['garments'][0]['warnings']
        self.assertIn('delicate cycle', garment_warnings)

    # -------------------------------------------------------------------------
    # Load sorting
    # -------------------------------------------------------------------------

    def test_loads_sorted_by_garment_count_desc(self):
        # 3 darks at 30C, 1 white at 30C -> darks load should come first
        darks = [
            make_garment(pk=i, color='black', washing='Machine wash cold (30°C)')
            for i in range(1, 4)
        ]
        white = make_garment(pk=10, color='white', washing='Machine wash cold (30°C)')
        result = group_into_loads(darks + [white])
        self.assertGreaterEqual(
            len(result['loads'][0]['garments']),
            len(result['loads'][-1]['garments']),
        )
        self.assertEqual(len(result['loads'][0]['garments']), 3)

    # -------------------------------------------------------------------------
    # Grouping key
    # -------------------------------------------------------------------------

    def test_grouping_key_color_temp_delicate(self):
        # Different color groups -> different loads
        g_dark = make_garment(pk=1, color='black', washing='Machine wash cold (30°C)')
        g_white = make_garment(pk=2, color='white', washing='Machine wash cold (30°C)')
        result = group_into_loads([g_dark, g_white])
        self.assertEqual(len(result['loads']), 2)
        color_groups = {load['color_group'] for load in result['loads']}
        self.assertIn('darks', color_groups)
        self.assertIn('whites', color_groups)

        # Same color, different temp -> different loads
        g1 = make_garment(pk=3, color='blue', washing='Cold wash only')
        g2 = make_garment(pk=4, color='blue', washing='Hot wash')
        result = group_into_loads([g1, g2])
        self.assertEqual(len(result['loads']), 2)

    def test_temperature_bucket_rounding(self):
        # 35°C -> rounds to 30 bucket (<=35)
        g = make_garment(washing='Wash at 35°C')
        result = group_into_loads([g])
        self.assertEqual(result['loads'][0]['temperature'], 30)

        # 36°C -> rounds to 40 bucket (36-50)
        g2 = make_garment(washing='Wash at 36°C')
        result2 = group_into_loads([g2])
        self.assertEqual(result2['loads'][0]['temperature'], 40)
