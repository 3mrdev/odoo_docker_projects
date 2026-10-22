# -*- coding: utf-8 -*-
"""Surgical portal updates batch:
1. providers only price/addon the vehicle types they have active vehicles for;
3. the pickup date is mandatory for the portal search;
4. the zone wizard exposes skip-existing as a provider-controlled checkbox;
5. the guest sign-in link leads to Odoo's real login and comes back."""

import re

from odoo.tests import HttpCase, tagged

from .common import LogspacePaymentCommon


@tagged('post_install', '-at_install')
class TestLogspacePortalUpdates(LogspacePaymentCommon, HttpCase):

    # ------------------------------------------------------------------
    # Task 1 - vehicle types scoped to active vehicles
    # ------------------------------------------------------------------

    def test_provider_active_vehicle_type_ids(self):
        """Only types with at least one ACTIVE vehicle surface."""
        Provider = self.env['res.partner']
        provider = Provider.create({'name': 'Scoped Provider', 'is_provider': True})
        type_active = self.env['logspace.vehicle.type'].create({
            'name': 'Scoped Active Type', 'code': 'scoped_active'})
        type_retired = self.env['logspace.vehicle.type'].create({
            'name': 'Scoped Retired Type', 'code': 'scoped_retired'})
        zone = self.env['logspace.zone'].create({
            'name': 'Scoped Zone', 'code': 'SCOPED-Z', 'zone_type': 'city'})
        for vtype, is_active in ((type_active, True), (type_retired, False)):
            self.env['logspace.vehicle'].create({
                'name': 'Scoped Vehicle %s' % vtype.code,
                'provider_id': provider.id,
                'vehicle_type_id': vtype.id,
                'plate_number': vtype.code,
                'zone_id': zone.id,
                'is_active': is_active,
            })
        self.assertIn(type_active, provider.logspace_active_vehicle_type_ids)
        self.assertNotIn(type_retired, provider.logspace_active_vehicle_type_ids)

    # ------------------------------------------------------------------
    # Task 3 - the pickup date is mandatory
    # ------------------------------------------------------------------

    def _post_search(self, data):
        """POST the search form the way the browser does: the route is
        csrf=True, so grab the hidden token from a fresh page first."""
        self.authenticate(None, None)
        page = self.url_open('/logspace')
        match = re.search(
            r'name="csrf_token"[^>]*value="([^"]+)"', page.text)
        if not match:
            match = re.search(
                r'value="([^"]+)"[^>]*name="csrf_token"', page.text)
        data['csrf_token'] = match.group(1)
        return self.url_open('/logspace', data=data)

    def test_search_without_date_is_rejected(self):
        response = self._post_search({})
        self.assertEqual(response.status_code, 200, response.text[:500])
        self.assertIn('Please choose a pickup date', response.text)

    def test_search_with_date_shows_no_error(self):
        response = self._post_search({'pickup_date': '2026-12-01'})
        self.assertEqual(response.status_code, 200, response.text[:500])
        self.assertNotIn('Please choose a pickup date', response.text)

    def test_search_date_input_is_required(self):
        self.authenticate(None, None)
        html = self.url_open('/logspace').text
        date_input = re.search(r'<input type="date"[^>]*>', html).group(0)
        self.assertIn('required="required"', date_input)

    # ------------------------------------------------------------------
    # Task 4 - skip-existing is a checkbox, default ON
    # ------------------------------------------------------------------

    def _make_wizard(self, skip_existing, existing_price):
        zone_a = self.env['logspace.zone'].create({
            'name': 'Skip Zone A', 'code': 'SKIP-A', 'zone_type': 'city'})
        zone_b = self.env['logspace.zone'].create({
            'name': 'Skip Zone B', 'code': 'SKIP-B', 'zone_type': 'city'})
        provider = self.env['res.partner'].create({
            'name': 'Skip Test Provider', 'is_provider': True})
        vtype = self.env['logspace.vehicle.type'].create({
            'name': 'Skip Test Type', 'code': 'SKIP-TYPE'})
        self.env['logspace.zone.distance'].create({
            'zone_from_id': zone_a.id, 'zone_to_id': zone_b.id,
            'estimated_km': 50.0,
        })
        self.env['logspace.price.matrix'].create({
            'provider_id': provider.id,
            'vehicle_type_id': vtype.id,
            'zone_from_id': zone_a.id,
            'zone_to_id': zone_b.id,
            'customer_price': existing_price,
            'provider_price': existing_price,
            'platform_fee': 0.0,
            'is_active': True,
        })
        return self.env['logspace.zone.setup.wizard'].create({
            'provider_id': provider.id,
            'zone_ids': [(6, 0, [zone_a.id, zone_b.id])],
            'vehicle_type_ids': [(6, 0, [vtype.id])],
            'base_rate': 10.0,
            'per_km_rate': 1.0,
            'skip_existing': skip_existing,
        })

    def test_skip_existing_defaults_to_true(self):
        wizard = self.env['logspace.zone.setup.wizard'].new({})
        self.assertTrue(wizard.skip_existing)

    def test_skipped_routes_keep_their_price(self):
        wizard = self._make_wizard(skip_existing=True, existing_price=999.0)
        wizard.action_confirm()
        entry = self.env['logspace.price.matrix'].search([
            ('zone_from_id.code', '=', 'SKIP-A'),
            ('zone_to_id.code', '=', 'SKIP-B'),
        ])
        self.assertEqual(len(entry), 1)
        self.assertAlmostEqual(entry.provider_price, 999.0)

    def test_unticked_skip_overwrites_the_price(self):
        wizard = self._make_wizard(skip_existing=False, existing_price=999.0)
        wizard.action_confirm()
        entry = self.env['logspace.price.matrix'].search([
            ('zone_from_id.code', '=', 'SKIP-A'),
            ('zone_to_id.code', '=', 'SKIP-B'),
        ])
        self.assertEqual(len(entry), 1)
        # 10 + 50 x 1.0 - the new rates replaced 999
        self.assertAlmostEqual(entry.provider_price, 60.0)

    # ------------------------------------------------------------------
    # Task 5 - guest sign-in goes to Odoo's login and comes back
    # ------------------------------------------------------------------

    def _open_details_page(self):
        vtype = self.env['logspace.vehicle.type'].create({
            'name': 'Guest Test Type', 'code': 'GUEST-TYPE'})
        zone_a = self.env['logspace.zone'].create({
            'name': 'Guest Zone A', 'code': 'GUEST-A', 'zone_type': 'city'})
        zone_b = self.env['logspace.zone'].create({
            'name': 'Guest Zone B', 'code': 'GUEST-B', 'zone_type': 'city'})
        provider = self.env['res.partner'].create({
            'name': 'Guest Test Provider', 'is_provider': True,
            'state': 'approved'})
        vehicle = self.env['logspace.vehicle'].create({
            'name': 'Guest Test Vehicle',
            'provider_id': provider.id,
            'vehicle_type_id': vtype.id,
            'plate_number': 'GUEST-1',
            'zone_id': zone_a.id,
            'is_active': True,
        })
        matrix = self.env['logspace.price.matrix'].create({
            'provider_id': provider.id,
            'vehicle_type_id': vtype.id,
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
            f'?provider_id={provider.id}&vehicle_type_id={vtype.id}'
            f'&vehicle_id={vehicle.id}&zone_from_id={zone_a.id}&zone_to_id={zone_b.id}'
            f'&matrix_id={matrix.id}&price=100.0'
        )

    def test_guest_sign_in_link_targets_odoo_login_with_redirect(self):
        response = self._open_details_page()
        self.assertEqual(response.status_code, 200, response.text[:500])
        self.assertIn('/web/login?redirect=/logspace/booking/details', response.text)
        self.assertNotIn('href="/logspace/login"', response.text)

    # ------------------------------------------------------------------
    # Retired mockup login/signup pages redirect to Odoo's real endpoints
    # ------------------------------------------------------------------

    def test_login_route_redirects_to_odoo_login(self):
        self.authenticate(None, None)
        response = self.url_open('/logspace/login')
        self.assertEqual(response.status_code, 200, response.text[:500])
        self.assertIn('/web/login', response.url)

    def test_login_route_keeps_the_redirect_param(self):
        self.authenticate(None, None)
        response = self.url_open('/logspace/login?redirect=/logspace/my')
        self.assertEqual(response.status_code, 200, response.text[:500])
        self.assertIn('redirect=%2Flogspace%2Fmy', response.url)

    def test_signup_route_redirects_to_odoo_signup(self):
        self.authenticate(None, None)
        response = self.url_open('/logspace/signup')
        self.assertEqual(response.status_code, 200, response.text[:500])
        self.assertIn('/web/signup', response.url)

    def test_mockup_pages_are_gone(self):
        self.authenticate(None, None)
        response = self.url_open('/logspace/login')
        self.assertNotIn('Welcome Back', response.text)
        response = self.url_open('/logspace/signup')
        self.assertNotIn('Create Account', response.text)
