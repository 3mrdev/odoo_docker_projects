# -*- coding: utf-8 -*-

import json
import re

from odoo import Command
from odoo.tests import HttpCase, tagged

from .common import LogspacePaymentCommon


@tagged('post_install', '-at_install')
class TestLogspaceVehicleCategory(LogspacePaymentCommon, HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Category = cls.env['logspace.vehicle.category']
        cls.VehicleType = cls.env['logspace.vehicle.type']

        cls.category_light = cls.env.ref('appness_logspace.vehicle_category_light')
        cls.category_medium = cls.env.ref('appness_logspace.vehicle_category_medium')

        # A type the category filter can drop (the seeded types cover the other
        # categories, so make an extra one to keep the assertions local).
        cls.vtype_light = cls.VehicleType.create({
            'name': 'Category Test Light',
            'code': 'cat_test_light',
            'category_id': cls.category_light.id,
        })
        cls.vtype_medium = cls.VehicleType.create({
            'name': 'Category Test Medium',
            'code': 'cat_test_medium',
            'category_id': cls.category_medium.id,
        })

    def test_seed_categories_exist(self):
        """The 4 seeded categories reproduce the old Selection exactly."""
        for code, name in (
            ('light', 'Light'), ('medium', 'Medium'),
            ('heavy', 'Heavy'), ('special', 'Special'),
        ):
            category = self.env.ref(f'appness_logspace.vehicle_category_{code}')
            self.assertEqual(category.code, code)
            self.assertEqual(category.name, name)

    def test_seeded_vehicle_types_are_categorised(self):
        """Every seeded type points at a category (would fail on a fresh install)."""
        for xmlid in (
            'vehicle_type_flatbed_3t', 'vehicle_type_flatbed_5t',
            'vehicle_type_covered_3t', 'vehicle_type_van',
            'vehicle_type_refrigerated', 'vehicle_type_minibus',
        ):
            vtype = self.env.ref(f'appness_logspace.{xmlid}')
            self.assertTrue(vtype.category_id, xmlid)

    def test_image_url_falls_back_on_unknown_code(self):
        """The category fallback is keyed on the category CODE.

        The old code did dict.get(<m2o recordset>), which raises
        TypeError: unhashable type - and only for types with no image and a
        code none of the default_images keys match.
        """
        vtype = self.VehicleType.create({
            'name': 'Exotic Mover',
            'code': 'exotic_mover',
            'category_id': self.category_light.id,
        })
        self.assertFalse(vtype.image)
        self.assertTrue(
            vtype.image_url.startswith('/appness_logspace/static/src/img/'),
            vtype.image_url,
        )
        # The light category maps to truck_mini.jpg
        self.assertEqual(vtype.image_url, '/appness_logspace/static/src/img/truck_mini.jpg')

    def test_image_url_uses_code_before_category(self):
        vtype = self.VehicleType.create({
            'name': 'Reefer Mover',
            'code': 'reefer_mover',
            'category_id': self.category_light.id,
        })
        self.assertEqual(vtype.image_url, '/appness_logspace/static/src/img/truck_reefer.jpg')

    def test_vehicle_info_page_renders_category_name(self):
        """The old template read vehicle_type._fields['category'].selection,
        which raises AttributeError on a Many2one - and this page sits on the
        mandatory path between search and booking."""
        self.authenticate(None, None)
        response = self.url_open(f'/logspace/vendor/vehicle/0?vehicle_type_id={self.vtype_light.id}')
        # No real vehicle exists, so the controller redirects back to the
        # search page; the assertion is that it does NOT raise a 500.
        self.assertEqual(response.status_code, 200, response.text[:500])

    # ---------------------------------------------------------------------
    # Search page
    # ---------------------------------------------------------------------

    def _search_page_html(self, query=''):
        self.authenticate(None, None)
        return self.url_open(f'/logspace{query}').text

    def test_search_page_renders_category_select_without_timeframe(self):
        html = self._search_page_html()
        self.assertIn('name="vehicle_category_id"', html)
        self.assertIn('name="vehicle_type_id"', html)   # non-vacuity: the page renders selects
        self.assertNotIn('name="pickup_timeframe"', html)

    def test_search_page_type_options_filtered_by_category(self):
        html = self._search_page_html(f'?vehicle_category_id={self.category_light.id}')
        select_html = html.split('name="vehicle_type_id"', 1)[1].split('</select>', 1)[0]
        option_values = re.findall(r'value="(\d+)"', select_html)
        self.assertIn(str(self.vtype_light.id), option_values)
        self.assertNotIn(str(self.vtype_medium.id), option_values)

    def test_search_page_pagination_preserves_category(self):
        html = self._search_page_html(f'?vehicle_category_id={self.category_light.id}&page=1')
        self.assertIn('vehicle_category_id', html)
        self.assertIn('name="vehicle_category_id"', html)   # non-vacuity

    def test_search_page_types_json_blob(self):
        html = self._search_page_html()
        self.assertIn('logspace-vehicle-types-data', html)
        script = html.split('logspace-vehicle-types-data', 1)[1].split('>', 1)[1].split('</script>', 1)[0]
        data = json.loads(script.strip())
        self.assertTrue(data)
        self.assertIn('category_id', data[0])
        self.assertIn('name', data[0])

    # ---------------------------------------------------------------------
    # Booking details page
    # ---------------------------------------------------------------------

    def _open_details_page(self, vehicle_type):
        """Drive the booking flow far enough for the details page to render.

        _get_validated_booking_data re-resolves every identifier server-side:
        the matrix must be active and consistent, the provider approved, the
        vehicle active, of the right type and based in the pickup zone
        hierarchy - so the fixture must satisfy all of it or the route
        silently bounces back to /logspace/search.
        """
        zone_a = self.env['logspace.zone'].create({
            'name': 'CatZone A', 'code': 'cat_zone_a', 'active': True, 'zone_type': 'city'})
        zone_b = self.env['logspace.zone'].create({
            'name': 'CatZone B', 'code': 'cat_zone_b', 'active': True, 'zone_type': 'city'})
        provider = self.env['res.partner'].create({
            'name': 'Category Test Provider',
            'is_provider': True,
            'is_company': True,
            'state': 'approved',
        })
        vehicle = self.env['logspace.vehicle'].create({
            'name': 'Category Test Vehicle',
            'provider_id': provider.id,
            'vehicle_type_id': vehicle_type.id,
            'plate_number': 'CAT-TEST-1',
            'zone_id': zone_a.id,
            'is_active': True,
        })
        matrix = self.env['logspace.price.matrix'].create({
            'provider_id': provider.id,
            'vehicle_type_id': vehicle_type.id,
            'zone_from_id': zone_a.id,
            'zone_to_id': zone_b.id,
            'customer_price': 100.0,
            'provider_price': 90.0,
            'platform_fee': 10.0,
            'is_active': True,
        })
        self.authenticate(None, None)
        return self.url_open(
            '/logspace/booking/details'
            f'?provider_id={provider.id}&vehicle_type_id={vehicle_type.id}'
            f'&vehicle_id={vehicle.id}&zone_from_id={zone_a.id}&zone_to_id={zone_b.id}'
            f'&matrix_id={matrix.id}&price=100.0'
        )

    def test_booking_details_renders_timeframe_select(self):
        response = self._open_details_page(self.vtype_light)
        self.assertEqual(response.status_code, 200, response.text[:500])
        self.assertIn('name="pickup_timeframe"', response.text)
        self.assertIn('<select', response.text)   # non-vacuity: it is a real select
        self.assertNotIn('form-control-plaintext', response.text.split('Pickup Timeframe')[1][:200])

    def test_time_slot_label_with_time(self):
        """Every slot label carries its window: "Morning (6:00 am - 11:59 am)"."""
        self.env['logspace.time.slot'].invalidate_recordset(['label_with_time'])
        labels = {
            slot.code: slot.label_with_time
            for slot in self.env['logspace.time.slot'].sudo().search([])
        }
        self.assertEqual(labels.get('morning'), 'Morning (6:00 am - 11:59 am)')
        self.assertEqual(labels.get('afternoon'), 'Afternoon (12:00 pm - 5:59 pm)')
        self.assertEqual(labels.get('evening'), 'Evening (6:00 pm - 11:59 pm)')
