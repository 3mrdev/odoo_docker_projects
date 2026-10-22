# -*- coding: utf-8 -*-

from types import SimpleNamespace
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

from ..controllers import common as common_controller


class TestLogspaceBookingSecurity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.zone_from = cls.env['logspace.zone'].create({
            'name': 'Security Test From',
            'code': 'SEC-FROM',
        })
        cls.zone_to = cls.env['logspace.zone'].create({
            'name': 'Security Test To',
            'code': 'SEC-TO',
        })
        cls.vehicle_type = cls.env['logspace.vehicle.type'].create({
            'name': 'Security Test Truck',
            'code': 'security-test-truck',
        })
        cls.provider = cls.env['res.partner'].create({
            'name': 'Security Test Provider',
            'is_provider': True,
            'is_approved_provider': True,
            'state': 'approved',
            'platform_fee_percentage': 0.1,
        })
        cls.vehicle = cls.env['logspace.vehicle'].create({
            'provider_id': cls.provider.id,
            'vehicle_type_id': cls.vehicle_type.id,
            'zone_id': cls.zone_from.id,
            'plate_number': 'SEC-PLATE-001',
        })
        cls.matrix = cls.env['logspace.price.matrix'].create({
            'provider_id': cls.provider.id,
            'vehicle_type_id': cls.vehicle_type.id,
            'zone_from_id': cls.zone_from.id,
            'zone_to_id': cls.zone_to.id,
            'provider_price': 100.0,
            'currency_id': cls.env.company.currency_id.id,
        })

    def _selection_values(self, **overrides):
        values = {
            'matrix_id': self.matrix.id,
            'provider_id': self.provider.id,
            'vehicle_type_id': self.vehicle_type.id,
            'zone_from_id': self.zone_from.id,
            'zone_to_id': self.zone_to.id,
            'vehicle_id': self.vehicle.id,
        }
        values.update(overrides)
        return values

    def test_selection_uses_server_matrix_price(self):
        selection = self.env['logspace.price.matrix']._validate_booking_selection(
            **self._selection_values()
        )

        self.assertEqual(selection['matrix'], self.matrix)
        self.assertEqual(selection['vehicle'], self.vehicle)
        self.assertEqual(selection['price'], self.matrix.customer_price)
        self.assertEqual(selection['price'], 110.0)

    def test_controller_ignores_forged_browser_price(self):
        booking_data = {
            'price_matrix_id': self.matrix.id,
            'provider_id': self.provider.id,
            'vehicle_type_id': self.vehicle_type.id,
            'zone_from_id': self.zone_from.id,
            'zone_to_id': self.zone_to.id,
            'vehicle_id': self.vehicle.id,
            'price': 0.01,
            'addon_ids': [],
        }
        fake_request = SimpleNamespace(env=self.env)

        with patch.object(common_controller, 'request', fake_request):
            trusted_data, _selection, _addons = (
                common_controller.LogspaceController()._get_validated_booking_data(
                    booking_data
                )
            )

        self.assertEqual(trusted_data['price'], self.matrix.customer_price)
        self.assertNotEqual(trusted_data['price'], booking_data['price'])

    def test_selection_rejects_mismatched_provider(self):
        attacker_provider = self.env['res.partner'].create({
            'name': 'Mismatched Provider',
            'is_provider': True,
            'state': 'approved',
        })

        with self.assertRaises(ValidationError):
            self.env['logspace.price.matrix']._validate_booking_selection(
                **self._selection_values(provider_id=attacker_provider.id)
            )

    def test_selection_rejects_inactive_vehicle(self):
        self.vehicle.is_active = False

        with self.assertRaises(ValidationError):
            self.env['logspace.price.matrix']._validate_booking_selection(
                **self._selection_values()
            )

    def test_selection_rejects_inactive_matrix(self):
        self.matrix.is_active = False

        with self.assertRaises(ValidationError):
            self.env['logspace.price.matrix']._validate_booking_selection(
                **self._selection_values()
            )

    def test_addon_uses_server_price_and_rejects_unoffered_addon(self):
        offered = self.env['logspace.addon'].create({
            'name': 'Offered Security Add-on',
            'code': 'security_offered',
            'price': 999.0,
            'currency_id': self.env.company.currency_id.id,
        })
        unoffered = self.env['logspace.addon'].create({
            'name': 'Unoffered Security Add-on',
            'code': 'security_unoffered',
            'price': 1.0,
            'currency_id': self.env.company.currency_id.id,
        })
        self.env['logspace.provider.vehicle.type.addon'].create({
            'provider_id': self.provider.id,
            'vehicle_type_id': self.vehicle_type.id,
            'addon_id': offered.id,
            'provider_price': 25.0,
            'currency_id': self.env.company.currency_id.id,
        })

        values = self.matrix._get_validated_booking_addons([offered.id, offered.id])
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]['addon'], offered)
        self.assertEqual(values[0]['price'], 25.0)

        with self.assertRaises(ValidationError):
            self.matrix._get_validated_booking_addons([unoffered.id])
