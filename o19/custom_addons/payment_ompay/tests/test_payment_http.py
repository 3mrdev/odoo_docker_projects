# Copyright 2026 Emad. Licensed under LGPL-3.0-or-later.

from unittest.mock import patch

from odoo.tests import tagged
from odoo.addons.payment.tests.http_common import PaymentHttpCommon
from odoo.addons.payment_ompay.controllers.main import OMPayController
from odoo.addons.payment_ompay.tests.common import OMPayCommon


@tagged('post_install', '-at_install')
class TestOMPayHttp(OMPayCommon, PaymentHttpCommon):
    """HTTP coverage for the public GET return route; no browser data becomes payment data."""

    def test_early_test_return_uses_inquiry_but_cannot_mark_payment_done(self):
        tx = self._create_ompay_transaction(
            provider_reference='11111111-1111-1111-1111-111111111111'
        )
        data = self._inquiry_data(status='SUCCESSFUL')
        url = self._build_url(
            f'{OMPayController._return_url}?reference_number={self.reference}'
            '&transaction_id=11111111-1111-1111-1111-111111111111'
            '&status=SUCCESSFUL&amount=999999&currency=USD'
        )
        with patch.object(type(tx), '_ompay_inquire', return_value=data) as inquiry:
            response = self.url_open(url, allow_redirects=False, timeout=60)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual(response.headers['Referrer-Policy'], 'no-referrer')
        inquiry.assert_called_once_with(transaction_id=tx.provider_reference)
        tx.invalidate_recordset(['state', 'state_message'])
        self.assertEqual(tx.state, 'done')

    def test_return_rejects_missing_or_mismatched_identifiers(self):
        missing_response = self._make_http_get_request(
            self._build_url(OMPayController._return_url), {}
        )
        self.assertEqual(missing_response.status_code, 403)
        mismatch_response = self._make_http_get_request(
            self._build_url(
                f'{OMPayController._return_url}?reference_number={self.reference}'
                '&transaction_id=22222222-2222-2222-2222-222222222222'
            ), {}
        )
        self.assertEqual(mismatch_response.status_code, 403)

    def test_terminal_return_replay_does_not_call_ompay_again(self):
        tx = self._create_ompay_transaction(
            provider_reference='11111111-1111-1111-1111-111111111111'
        )
        tx._set_done()
        url = self._build_url(
            f'{OMPayController._return_url}?reference_number={self.reference}'
            '&transaction_id=11111111-1111-1111-1111-111111111111'
        )
        with patch.object(type(tx), '_ompay_inquire') as inquiry:
            response = self.url_open(url, allow_redirects=False, timeout=60)
        self.assertEqual(response.status_code, 303)
        inquiry.assert_not_called()

    def test_return_recovers_missing_provider_reference_by_odoo_reference(self):
        tx = self._create_ompay_transaction(ompay_creation_attempted=True)
        tx._set_pending()
        data = self._inquiry_data(status='SUCCESSFUL')
        url = self._build_url(
            f'{OMPayController._return_url}?reference_number={self.reference}'
            '&transaction_id=11111111-1111-1111-1111-111111111111'
        )
        with patch.object(type(tx), '_ompay_inquire', return_value=data) as inquiry:
            response = self.url_open(url, allow_redirects=False, timeout=60)
        self.assertEqual(response.status_code, 303)
        inquiry.assert_called_once_with(reference_number=tx.reference)
        tx.invalidate_recordset(['provider_reference', 'state', 'state_message'])
        self.assertEqual(tx.provider_reference, data['transaction_id'])
        self.assertEqual(tx.state, 'done')

    def test_pending_return_replay_is_rate_limited(self):
        tx = self._create_ompay_transaction(
            provider_reference='11111111-1111-1111-1111-111111111111'
        )
        data = self._inquiry_data(status='PROCESSING')
        url = self._build_url(
            f'{OMPayController._return_url}?reference_number={self.reference}'
            '&transaction_id=11111111-1111-1111-1111-111111111111'
        )
        with patch.object(type(tx), '_ompay_inquire', return_value=data) as inquiry:
            first_response = self.url_open(url, allow_redirects=False, timeout=60)
            second_response = self.url_open(url, allow_redirects=False, timeout=60)

        self.assertEqual(first_response.status_code, 303)
        self.assertEqual(second_response.status_code, 303)
        inquiry.assert_called_once_with(transaction_id=tx.provider_reference)
        tx.invalidate_recordset(['ompay_last_return_inquiry_at', 'state'])
        self.assertTrue(tx.ompay_last_return_inquiry_at)
        self.assertEqual(tx.state, 'pending')
