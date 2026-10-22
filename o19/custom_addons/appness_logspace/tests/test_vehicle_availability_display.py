# -*- coding: utf-8 -*-

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import HttpCase, tagged


CUSTOMER_LOGIN = 'avail.customer.user@example.com'
CUSTOMER_PASSWORD = 'AvailTest!2026'


@tagged('post_install', '-at_install')
class TestLogspaceVehicleAvailabilityDisplay(HttpCase):
    """A booked vehicle stays out of search results until its order reaches
    the grace period, the vehicle code is not shown to customers before the
    dropoff is done, and every customer-facing timeframe shows its hours."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.zone_from = cls.env['logspace.zone'].create({
            'name': 'AvailZone A', 'code': 'avail_zone_a', 'active': True, 'zone_type': 'city'})
        cls.zone_to = cls.env['logspace.zone'].create({
            'name': 'AvailZone B', 'code': 'avail_zone_b', 'active': True, 'zone_type': 'city'})
        cls.provider = cls.env['res.partner'].create({
            'name': 'Availability Test Provider',
            'is_provider': True,
            'is_company': True,
            'state': 'approved',
        })
        cls.vehicle_type = cls.env['logspace.vehicle.type'].create({
            'name': 'Availability Test Type', 'code': 'avail_test_type'})
        cls.vehicle = cls.env['logspace.vehicle'].create({
            'name': 'Availability Test Vehicle',
            'provider_id': cls.provider.id,
            'vehicle_type_id': cls.vehicle_type.id,
            'plate_number': 'AVAIL-TEST-1',
            'zone_id': cls.zone_from.id,
            'is_active': True,
        })
        cls.matrix = cls.env['logspace.price.matrix'].create({
            'provider_id': cls.provider.id,
            'vehicle_type_id': cls.vehicle_type.id,
            'zone_from_id': cls.zone_from.id,
            'zone_to_id': cls.zone_to.id,
            'customer_price': 100.0,
            'provider_price': 90.0,
            'platform_fee': 10.0,
            'is_active': True,
        })
        cls.customer = cls.env['res.partner'].create({
            'name': 'Availability Test Customer',
            'email': 'avail.customer@example.com',
        })
        cls.customer_user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Availability Test Customer User',
            'login': CUSTOMER_LOGIN,
            'email': CUSTOMER_LOGIN,
            'password': CUSTOMER_PASSWORD,
            'partner_id': cls.customer.id,
            'group_ids': [Command.set([cls.env.ref('base.group_portal').id])],
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Availability Test Transport',
            'type': 'service',
            'list_price': 100.0,
        })

    def _make_paid_booking(self, state='order_received', date='2026-10-13'):
        """A confirmed, PAID Logspace order on the shared vehicle."""
        order = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'is_logspace_order': True,
            'logspace_provider_id': self.provider.id,
            'logspace_vehicle_id': self.vehicle.id,
            'scheduled_date': date,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        order.action_confirm()
        order.write({'payment_status': 'paid', 'logspace_state': state})
        return order

    # ---------------------------------------------------------------------
    # Model: booked vehicle hidden until grace period
    # ---------------------------------------------------------------------

    def test_free_vehicle_is_available_with_and_without_date(self):
        self.assertTrue(self.vehicle.is_available_on_date())
        self.assertTrue(self.vehicle.is_available_on_date('2026-10-13'))
        vehicles = self.env['logspace.vehicle'].get_available_vehicles(
            self.provider.id, self.vehicle_type.id, self.zone_from.id)
        self.assertIn(self.vehicle, vehicles)

    def test_paid_booking_hides_vehicle_until_grace_period(self):
        order = self._make_paid_booking('order_received')
        self.assertFalse(self.vehicle.is_available_on_date())
        self.assertFalse(self.vehicle.is_available_on_date('2026-10-13'))
        for date_str in (None, '2026-10-13'):
            vehicles = self.env['logspace.vehicle'].get_available_vehicles(
                self.provider.id, self.vehicle_type.id, self.zone_from.id,
                date_str=date_str)
            self.assertNotIn(self.vehicle, vehicles)
        order.logspace_state = 'grace_period'
        self.assertTrue(self.vehicle.is_available_on_date())
        vehicles = self.env['logspace.vehicle'].get_available_vehicles(
            self.provider.id, self.vehicle_type.id, self.zone_from.id)
        self.assertIn(self.vehicle, vehicles)

    def test_cancelled_booking_releases_vehicle(self):
        order = self._make_paid_booking('order_received')
        self.assertFalse(self.vehicle.is_available_on_date())
        order.logspace_state = 'cancelled'
        self.assertTrue(self.vehicle.is_available_on_date())

    def test_booked_vehicle_cannot_be_validated_for_a_new_booking(self):
        self._make_paid_booking('order_received')
        with self.assertRaises(ValidationError):
            self.env['logspace.price.matrix']._validate_booking_selection(
                matrix_id=self.matrix.id,
                provider_id=self.provider.id,
                vehicle_type_id=self.vehicle_type.id,
                zone_from_id=self.zone_from.id,
                zone_to_id=self.zone_to.id,
                vehicle_id=self.vehicle.id,
            )

    # ---------------------------------------------------------------------
    # Vehicle info page: no code, 2-day notice
    # ---------------------------------------------------------------------

    def _open_vehicle_info_page(self):
        self.authenticate(None, None)
        return self.url_open(
            '/logspace/vendor/vehicle/%d?provider_id=%d&vehicle_type_id=%d'
            '&zone_from_id=%d&zone_to_id=%d&matrix_id=%d'
            % (self.vehicle.id, self.provider.id, self.vehicle_type.id,
               self.zone_from.id, self.zone_to.id, self.matrix.id))

    def test_vehicle_info_page_hides_code_and_shows_2_day_notice(self):
        response = self._open_vehicle_info_page()
        self.assertEqual(response.status_code, 200, response.text[:500])
        self.assertIn('Book Now', response.text)   # non-vacuity: the page rendered
        self.assertNotIn('Vehicle Code:', response.text)
        self.assertIn('Estimated time after pickup is 2 days.', response.text)

    # ---------------------------------------------------------------------
    # Track page: code appears only after dropoff, timeframes carry hours
    # ---------------------------------------------------------------------

    def _track_page_html(self):
        self.authenticate(CUSTOMER_LOGIN, CUSTOMER_PASSWORD)
        response = self.url_open('/logspace/my/orders/track/%s' % self.order.name)
        self.assertEqual(response.status_code, 200, response.text[:500])
        return response.text

    def _make_tracked_order(self, **extra):
        self._make_paid_booking('order_received')
        self.order = self.env['sale.order'].search([
            ('is_logspace_order', '=', True),
            ('logspace_vehicle_id', '=', self.vehicle.id),
        ], limit=1)
        self.order.write(extra)
        self.env.flush_all()
        return self.order

    def test_track_page_hides_vehicle_code_before_dropoff(self):
        self._make_tracked_order()
        self.assertNotIn('Vehicle Code:', self._track_page_html())

    def test_track_page_shows_vehicle_code_after_dropoff_completed(self):
        self._make_tracked_order()
        for state in ('dropoff_completed', 'grace_period', 'order_completed'):
            with self.subTest(state=state):
                self.order.logspace_state = state
                self.env.flush_all()
                html = self._track_page_html()
                self.assertIn('Vehicle Code:', html)
                self.assertIn(self.vehicle.name, html)

    def test_track_page_timeframes_show_time_ranges(self):
        self._make_tracked_order(pickup_timeframe='afternoon', dropoff_timeframe='evening')
        html = self._track_page_html()
        self.assertIn('Afternoon (12:00 pm - 5:59 pm)', html)
        self.assertIn('Evening (6:00 pm - 11:59 pm)', html)
        self.assertNotIn('>Afternoon<', html)
        self.assertNotIn('>afternoon<', html)
