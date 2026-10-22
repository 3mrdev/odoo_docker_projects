# -*- coding: utf-8 -*-

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestLogspaceVerificationWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_provider = cls.env.ref('appness_logspace.group_logspace_provider')
        cls.provider_partner = cls.env['res.partner'].create({
            'name': 'Verification Test Provider',
            'is_provider': True,
            'state': 'approved',
        })
        cls.provider_user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Verification Test Provider User',
            'login': 'verification_test_provider@example.com',
            'email': 'verification_test_provider@example.com',
            'partner_id': cls.provider_partner.id,
            'group_ids': [Command.set([cls.group_provider.id])],
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Verification Test Transport',
            'type': 'service',
            'list_price': 100.0,
        })
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.provider_partner.id,
            'is_logspace_order': True,
            'logspace_provider_id': cls.provider_partner.id,
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        cls.order.action_confirm()

    def _wizard(self, code):
        return self.env['logspace.verification.wizard'].with_user(
            self.provider_user
        ).create({
            'order_id': self.order.id,
            'code_type': 'pickup',
            'entered_code': code,
        })

    def test_provider_cannot_write_logspace_state_directly(self):
        with self.assertRaises(UserError):
            self.order.with_user(self.provider_user.id).write({'logspace_state': 'pickup_completed'})
        self.assertEqual(self.order.logspace_state, 'order_received')

    def test_admin_can_write_logspace_state_directly(self):
        self.order.write({'logspace_state': 'pickup_completed'})
        self.assertEqual(self.order.logspace_state, 'pickup_completed')

    def test_provider_pickup_button_opens_wizard(self):
        order = self.order.with_user(self.provider_user.id)
        order.action_start_pickup()
        result = order.action_pickup_completed()
        self.assertEqual(result['res_model'], 'logspace.verification.wizard')
        self.assertEqual(result['context']['default_code_type'], 'pickup')
        self.assertEqual(self.order.logspace_state, 'pickup_started')

    def test_admin_pickup_button_bypasses_wizard(self):
        self.order.action_start_pickup()
        result = self.order.action_pickup_completed()
        self.assertTrue(result)
        self.assertEqual(self.order.logspace_state, 'pickup_completed')

    def test_wizard_rejects_wrong_code(self):
        self.order.with_user(self.provider_user.id).action_start_pickup()
        wizard = self._wizard('0000')
        self.assertNotEqual(wizard.entered_code, self.order.verification_code_pickup)
        with self.assertRaises(UserError):
            wizard.action_verify()
        self.assertEqual(self.order.logspace_state, 'pickup_started')

    def test_wizard_accepts_correct_code(self):
        self.order.with_user(self.provider_user.id).action_start_pickup()
        wizard = self._wizard(self.order.verification_code_pickup)
        wizard.action_verify()
        self.assertEqual(self.order.logspace_state, 'pickup_completed')

    def test_dropoff_requires_dropoff_code(self):
        self.order.with_user(self.provider_user.id).action_start_pickup()
        # Advance through the wizard path to pickup_completed
        wizard = self.env['logspace.verification.wizard'].with_user(
            self.provider_user
        ).create({
            'order_id': self.order.id,
            'code_type': 'pickup',
            'entered_code': self.order.verification_code_pickup,
        })
        wizard.action_verify()

        self.order.with_user(self.provider_user.id).action_arrived_destination()
        self.assertTrue(self.order.verification_code_dropoff)

        # Wrong dropoff code is rejected
        dropoff_wizard = self.env['logspace.verification.wizard'].with_user(
            self.provider_user
        ).create({
            'order_id': self.order.id,
            'code_type': 'dropoff',
            'entered_code': self.order.verification_code_pickup,  # wrong: pickup code
        })
        with self.assertRaises(UserError):
            dropoff_wizard.action_verify()
        self.assertEqual(self.order.logspace_state, 'arrived_destination')

        # Correct dropoff code completes the drop-off
        dropoff_wizard.entered_code = self.order.verification_code_dropoff
        dropoff_wizard.action_verify()
        self.assertEqual(self.order.logspace_state, 'dropoff_completed')
        self.assertTrue(self.order.delivery_date)
