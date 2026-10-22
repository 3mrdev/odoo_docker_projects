# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LogspacePaymentCommon


@tagged('post_install', '-at_install')
class TestLogspacePaymentLifecycle(LogspacePaymentCommon):

    def test_draft_has_no_fulfillment_state_or_verification_codes(self):
        self.assertEqual(self.order.state, 'draft')
        self.assertFalse(self.order.logspace_state)
        self.assertFalse(self.order.verification_code_pickup)
        self.assertFalse(self.order.verification_code_dropoff)

    def test_confirmation_finalizer_is_idempotent(self):
        self.order.action_confirm()

        self.assertEqual(self.order.state, 'sale')
        self.assertEqual(self.order.logspace_state, 'order_received')
        self.assertTrue(self.order.logspace_confirmation_processed)
        self.assertRegex(self.order.verification_code_pickup, r'^\d{4}$')
        self.assertFalse(self.order.verification_code_dropoff)
        self.assertEqual(
            len(self.order.timeline_ids.filtered(
                lambda event: event.event_type == 'order_received'
            )),
            1,
        )

        self.order._finalize_logspace_confirmation()
        self.assertEqual(
            len(self.order.timeline_ids.filtered(
                lambda event: event.event_type == 'order_received'
            )),
            1,
        )

    def test_unconfirmed_order_cannot_start_fulfillment(self):
        self.order.logspace_state = 'order_received'
        with self.assertRaises(UserError):
            self.order.action_start_pickup()
        self.assertEqual(self.order.logspace_state, 'order_received')

    def test_success_has_priority_over_later_failure(self):
        successful_tx = self._create_logspace_transaction(reference='LOG-SUCCESS')
        successful_tx._set_done()
        failed_tx = self._create_logspace_transaction(reference='LOG-FAILURE')
        failed_tx._set_error('Declined in test')

        self.order._sync_logspace_payment_fields()

        self.assertEqual(self.order.payment_status, 'paid')
        self.assertEqual(self.order.transaction_ref, successful_tx.reference)
        self.assertEqual(
            len(self.order.timeline_ids.filtered(
                lambda event: event.event_type == 'payment_received'
            )),
            1,
        )

    def test_pending_and_failed_states_are_not_paid(self):
        pending_tx = self._create_logspace_transaction(reference='LOG-PENDING')
        pending_tx._set_pending()
        self.order._sync_logspace_payment_fields()
        self.assertEqual(self.order.payment_status, 'pending')
        self.assertEqual(self.order.state, 'draft')

        pending_tx._set_error('Timed out in test')
        self.order._sync_logspace_payment_fields()
        self.assertEqual(self.order.payment_status, 'failed')
        self.assertEqual(self.order.state, 'draft')

    def test_partial_success_is_not_reported_as_fully_paid(self):
        transaction = self._create_logspace_transaction(
            amount=self.order.amount_total / 2, reference='LOG-PARTIAL',
        )
        transaction._set_done()

        self.order._sync_logspace_payment_fields()

        self.assertEqual(self.order.payment_status, 'pending')
        self.assertEqual(self.order.state, 'draft')
        self.assertFalse(self.order.timeline_ids.filtered(
            lambda event: event.event_type == 'payment_received'
        ))

    def test_paid_sync_confirms_order_without_post_process(self):
        """A paid order must never stay a quotation, even when the sync is
        reached on a path that bypasses core's auto-confirm (later manual
        link, migration backfill)."""
        transaction = self._create_logspace_transaction(
            reference='LOG-SYNC-CONFIRM',
        )
        transaction._set_done()

        self.order._sync_logspace_payment_fields()

        self.assertEqual(self.order.state, 'sale')
        self.assertEqual(self.order.payment_status, 'paid')
        self.assertEqual(self.order.logspace_state, 'order_received')
        self.assertTrue(self.order.logspace_confirmation_processed)
        self.assertRegex(self.order.verification_code_pickup, r'^\d{4}$')
        self.assertEqual(
            len(self.order.timeline_ids.filtered(
                lambda event: event.event_type == 'order_received'
            )),
            1,
        )
        # Idempotent: a second sync after confirmation changes nothing.
        self.order._sync_logspace_payment_fields()
        self.assertEqual(self.order.state, 'sale')
        self.assertEqual(
            len(self.order.timeline_ids.filtered(
                lambda event: event.event_type == 'order_received'
            )),
            1,
        )

    def test_legacy_link_is_canonicalized_before_standard_post_processing(self):
        transaction = self._create_logspace_transaction(
            legacy_link=True, reference='LOG-LEGACY-AUTHORIZED',
        )
        transaction.provider_id.support_manual_capture = 'full_only'
        transaction._set_authorized()

        with patch.object(type(self.order), '_send_payment_succeeded_for_order_mail'):
            transaction._post_process()

        self.assertIn(self.order, transaction.sale_order_ids)
        self.assertEqual(self.order.state, 'sale')
        self.assertEqual(self.order.payment_status, 'paid')
        self.assertTrue(self.order.logspace_confirmation_processed)

    def test_dropoff_code_is_generated_only_at_destination(self):
        self.order.action_confirm()
        self.order.logspace_state = 'pickup_completed'
        self.assertFalse(self.order.verification_code_dropoff)

        self.order.action_arrived_destination()

        self.assertRegex(self.order.verification_code_dropoff, r'^\d{4}$')

    def test_paid_sets_logspace_state_and_pickup_code(self):
        self.assertFalse(self.order.logspace_state)
        tx = self._create_logspace_transaction(reference='LOG-PAID-TEST')
        tx._set_done()
        self.order._sync_logspace_payment_fields()

        self.assertEqual(self.order.payment_status, 'paid')
        self.assertEqual(self.order.logspace_state, 'order_received')
        self.assertTrue(self.order.logspace_confirmation_processed)
        self.assertRegex(self.order.verification_code_pickup, r'^\d{4}$')

    def test_order_completion_creates_provider_bill(self):
        provider = self.env['res.partner'].create({
            'name': 'Test Provider Logistics',
            'is_provider': True,
            'state': 'approved',
            'platform_fee_percentage': 0.1,  # 10%
        })
        self.order.write({
            'logspace_provider_id': provider.id,
        })
        self.order.action_confirm()
        self.order.logspace_state = 'dropoff_completed'

        self.assertFalse(self.order.logspace_provider_bill_id)
        self.assertEqual(self.order.logspace_provider_bill_count, 0)

        self.order.action_complete_order()

        self.assertEqual(self.order.logspace_state, 'order_completed')
        self.assertTrue(self.order.logspace_provider_bill_id)
        self.assertEqual(self.order.logspace_provider_bill_count, 1)

        bill = self.order.logspace_provider_bill_id
        self.assertEqual(bill.move_type, 'in_invoice')
        self.assertEqual(bill.partner_id, provider)
        self.assertEqual(len(bill.invoice_line_ids), 1)
        # B5: the bill is posted on creation, so a provider's bill list never
        # silently looks empty.
        self.assertEqual(bill.state, 'posted')
        # Order total is 100, 10% fee = 10, provider amount = 90
        self.assertAlmostEqual(bill.invoice_line_ids[0].price_unit, 90.0)
        self.assertAlmostEqual(self.order.logspace_provider_bill_amount, 90.0)
        self.assertAlmostEqual(self.order.logspace_provider_commission_rate, 0.1)

    def test_admin_complete_order_creates_provider_bill(self):
        provider = self.env['res.partner'].create({
            'name': 'Admin Test Provider',
            'is_provider': True,
            'state': 'approved',
            'platform_fee_percentage': 0.15,  # 15%
        })
        self.order.write({
            'logspace_provider_id': provider.id,
        })
        self.order.action_confirm()

        self.order.action_admin_complete_order()

        self.assertEqual(self.order.logspace_state, 'order_completed')
        self.assertTrue(self.order.logspace_provider_bill_id)
        bill = self.order.logspace_provider_bill_id
        # Order total is 100, 15% fee = 15, provider amount = 85
        self.assertAlmostEqual(bill.invoice_line_ids[0].price_unit, 85.0)
