# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import fields
from odoo.tests import JsonRpcException, tagged

from odoo.addons.payment.tests.http_common import PaymentHttpCommon

from .common import LogspacePaymentCommon


@tagged('post_install', '-at_install')
class TestLogspacePaymentHttp(LogspacePaymentCommon, PaymentHttpCommon):

    def _payment_url(self):
        token = self.order._portal_ensure_token()
        return self._build_url(
            f'/logspace/booking/payment/{self.order.id}?access_token={token}'
        )

    def _transaction_values(self, **overrides):
        values = {
            'access_token': self.order._portal_ensure_token(),
            'provider_id': self.provider.id,
            'payment_method_id': self.payment_method.id,
            'token_id': None,
            'amount': self.order.amount_total,
            'flow': 'redirect',
            'tokenization_requested': False,
            'landing_route': '/untrusted-browser-route',
            'is_validation': False,
        }
        values.update(overrides)
        return values

    def _transaction_route(self):
        return self._build_url(
            f'/logspace/booking/payment/transaction/{self.order.id}'
        )

    def test_legacy_done_route_cannot_confirm_without_token(self):
        response = self.url_open(
            self._build_url(f'/logspace/booking/done?order_id={self.order.id}'),
            allow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.order.invalidate_recordset()
        self.assertEqual(self.order.state, 'draft')
        self.assertFalse(self.order.timeline_ids)

    def test_result_route_requires_order_access_token_and_is_read_only(self):
        missing_token_response = self.url_open(
            self._build_url(f'/logspace/booking/payment/result/{self.order.id}'),
            allow_redirects=False,
        )
        self.assertEqual(missing_token_response.status_code, 303)

        token = self.order._portal_ensure_token()
        valid_response = self.url_open(
            self._build_url(
                f'/logspace/booking/payment/result/{self.order.id}?access_token={token}'
            ),
            allow_redirects=False,
        )
        self.assertEqual(valid_response.status_code, 200)
        self.assertEqual(valid_response.headers['Cache-Control'], 'no-store')
        self.assertEqual(valid_response.headers['Referrer-Policy'], 'no-referrer')
        self.order.invalidate_recordset()
        self.assertEqual(self.order.state, 'draft')

    def test_cross_order_token_and_non_logspace_order_are_rejected(self):
        other_order = self.order.copy({'is_logspace_order': True})
        other_token = other_order._portal_ensure_token()
        cross_order_response = self.url_open(
            self._build_url(
                f'/logspace/booking/payment/{self.order.id}?access_token={other_token}'
            ),
            allow_redirects=False,
        )
        self.assertEqual(cross_order_response.status_code, 303)

        ordinary_order = self.order.copy({'is_logspace_order': False})
        ordinary_token = ordinary_order._portal_ensure_token()
        ordinary_response = self.url_open(
            self._build_url(
                f'/logspace/booking/payment/{ordinary_order.id}'
                f'?access_token={ordinary_token}'
            ),
            allow_redirects=False,
        )
        self.assertEqual(ordinary_response.status_code, 303)

    def test_public_payment_page_never_exposes_saved_tokens(self):
        self._create_token(partner_id=self.order.partner_id.id)

        response = self.url_open(self._payment_url())
        context = self._get_payment_context(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual(response.headers['Referrer-Policy'], 'no-referrer')
        self.assertFalse(context['token_ids'])
        self.assertIn(self.payment_method.id, context['payment_method_ids'])

    def test_transaction_uses_authoritative_order_values_and_standard_link(self):
        processing_values = self.make_jsonrpc_request(
            self._transaction_route(), self._transaction_values(),
        )
        transaction = self.order.transaction_ids.sorted('id', reverse=True)[:1]

        self.assertTrue(processing_values)
        self.assertTrue(transaction)
        self.assertEqual(transaction.amount, self.order.amount_total)
        self.assertEqual(transaction.currency_id, self.order.currency_id)
        self.assertEqual(transaction.partner_id, self.order.partner_id)
        self.assertEqual(transaction.logspace_order_id, self.order)
        self.assertIn(self.order, transaction.sale_order_ids)
        self.assertNotEqual(transaction.landing_route, '/untrusted-browser-route')
        self.assertIn('access_token=', transaction.landing_route)

    def test_transaction_rejects_tampered_amount_and_unknown_kwargs(self):
        with self.assertRaises(JsonRpcException):
            self.make_jsonrpc_request(
                self._transaction_route(), self._transaction_values(amount=1.0),
            )
        with self.assertRaises(JsonRpcException):
            self.make_jsonrpc_request(
                self._transaction_route(), self._transaction_values(partner_id=999999),
            )
        self.assertFalse(self.order.transaction_ids)

    def test_transaction_rejects_unavailable_provider(self):
        self.provider.state = 'disabled'

        with self.assertRaises(JsonRpcException):
            self.make_jsonrpc_request(
                self._transaction_route(), self._transaction_values(),
            )

        self.assertFalse(self.order.transaction_ids)

    def test_public_user_cannot_forge_saved_token_flow(self):
        token = self._create_token(partner_id=self.order.partner_id.id)

        with self.assertRaises(JsonRpcException):
            self.make_jsonrpc_request(
                self._transaction_route(),
                self._transaction_values(
                    flow='token', token_id=token.id, payment_method_id=None,
                ),
            )

        self.assertFalse(self.order.transaction_ids)

    def test_recent_draft_blocks_duplicates_but_abandoned_draft_can_retry(self):
        self.make_jsonrpc_request(self._transaction_route(), self._transaction_values())
        first_transaction = self.order.transaction_ids.sorted('id', reverse=True)[:1]

        with self.assertRaises(JsonRpcException):
            self.make_jsonrpc_request(self._transaction_route(), self._transaction_values())

        old_create_date = fields.Datetime.now() - timedelta(minutes=31)
        self.env.cr.execute(
            'UPDATE payment_transaction SET create_date = %s WHERE id = %s',
            (old_create_date, first_transaction.id),
        )
        first_transaction.invalidate_recordset(['create_date'])

        self.make_jsonrpc_request(self._transaction_route(), self._transaction_values())
        self.assertEqual(len(self.order.transaction_ids), 2)
