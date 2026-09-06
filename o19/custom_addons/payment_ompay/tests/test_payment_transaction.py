# Copyright 2026 Emad. Licensed under LGPL-3.0-or-later.

from unittest.mock import patch

import requests
from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import ValidationError

from odoo.addons.payment_ompay import const
from odoo.addons.payment_ompay.tests.common import OMPayCommon


class TestOMPayTransaction(OMPayCommon):

    def test_bank_hosted_creation_payload_redirect_and_reference(self):
        tx = self._create_ompay_transaction()
        provider_reference = '11111111-1111-1111-1111-111111111111'
        redirect_url = (
            'https://api.sandbox.truepay.ompay.om/api/v1/transactions/'
            f'{provider_reference}/pay-page'
        )
        response = self._response({
            'transaction_id': provider_reference,
            'status': 'PROCESSING',
            'redirect_url': redirect_url,
        })
        with patch.object(
            type(self.provider), '_send_api_request', return_value=response
        ) as send_request:
            processing_values = tx._get_processing_values()

        payload = send_request.call_args.kwargs['json']
        self.assertEqual(send_request.call_args.args, ('POST', const.BANK_HOSTED_ENDPOINT))
        self.assertEqual(send_request.call_args.kwargs['reference'], self.reference)
        self.assertEqual(payload['amount'], 12.5)
        self.assertEqual(payload['currency'], 'OMR')
        self.assertEqual(payload['reference_number'], self.reference)
        self.assertTrue(payload['return_url'].endswith('/payment/ompay/return'))
        self.assertEqual(
            self.provider.redirect_form_view_id, self.env.ref('payment_ompay.redirect_form')
        )
        rendered_form = str(processing_values['redirect_form_html'])
        self.assertIn('<form', rendered_form)
        self.assertIn(f'action="{redirect_url}"', rendered_form)
        self.assertIn('method="get"', rendered_form)
        self.assertNotIn('<input', rendered_form)
        self.assertEqual(tx.provider_reference, provider_reference)
        self.assertEqual(tx.state, 'pending')

    def test_nonstandard_transport_failure_keeps_creation_recoverable(self):
        tx = self._create_ompay_transaction()
        inquiry_response = requests.Response()
        inquiry_response.status_code = 200
        inquiry_response.url = self.provider._build_request_url(const.INQUIRY_ENDPOINT)
        inquiry_response._content = (
            b'{"success": true, "data": {'
            b'"transaction_id": "11111111-1111-1111-1111-111111111111", '
            b'"reference_number": "OMPay-TEST-001", "status": "PROCESSING", '
            b'"amount": "12.500", "currency": "OMR"}}'
        )

        with patch.object(
            requests,
            'request',
            side_effect=[
                requests.exceptions.ChunkedEncodingError('truncated create response'),
                inquiry_response,
            ],
        ) as request:
            rendering_values = tx._get_specific_rendering_values({})

        self.assertEqual(request.call_count, 2)
        self.assertTrue(request.call_args_list[0].args[1].endswith(const.BANK_HOSTED_ENDPOINT))
        self.assertTrue(request.call_args_list[1].args[1].endswith(const.INQUIRY_ENDPOINT))
        self.assertTrue(tx.ompay_creation_attempted)
        self.assertEqual(
            tx.provider_reference, '11111111-1111-1111-1111-111111111111'
        )
        self.assertEqual(tx.state, 'pending')
        self.assertIn('/pay-page', rendering_values['api_url'])

    def test_duplicate_reference_response_recovers_by_inquiry_without_another_create(self):
        tx = self._create_ompay_transaction()
        duplicate_response = requests.Response()
        duplicate_response.status_code = 409
        duplicate_response.url = self.provider._build_request_url(const.BANK_HOSTED_ENDPOINT)
        duplicate_response._content = (
            b'{"error":"DUPLICATE_ENTRY","message":"unsafe provider diagnostic"}'
        )
        inquiry_response = requests.Response()
        inquiry_response.status_code = 200
        inquiry_response.url = self.provider._build_request_url(const.INQUIRY_ENDPOINT)
        inquiry_response._content = (
            b'{"success": true, "data": {'
            b'"transaction_id": "11111111-1111-1111-1111-111111111111", '
            b'"reference_number": "OMPay-TEST-001", "status": "PROCESSING", '
            b'"amount": "12.500", "currency": "OMR"}}'
        )

        with patch.object(
            requests, 'request', side_effect=[duplicate_response, inquiry_response]
        ) as request:
            rendering_values = tx._get_specific_rendering_values({})

        self.assertEqual(request.call_count, 2)
        self.assertTrue(request.call_args_list[0].args[1].endswith(const.BANK_HOSTED_ENDPOINT))
        self.assertTrue(request.call_args_list[1].args[1].endswith(const.INQUIRY_ENDPOINT))
        self.assertTrue(tx.ompay_creation_attempted)
        self.assertEqual(
            tx.provider_reference, '11111111-1111-1111-1111-111111111111'
        )
        self.assertEqual(tx.state, 'pending')
        self.assertIn('/pay-page', rendering_values['api_url'])

    def test_rejects_open_redirect_and_untrusted_create_data(self):
        tx = self._create_ompay_transaction()
        response = self._response({
            'transaction_id': '11111111-1111-1111-1111-111111111111',
            'status': 'PROCESSING',
            'redirect_url': 'https://evil.example/api/v1/transactions/111/pay-page',
        })
        with patch.object(
            type(tx), '_send_api_request', side_effect=[response, ValidationError('x')]
        ):
            self.assertEqual(tx._get_specific_rendering_values({}), {
                'api_url': '/payment/status', 'url_params': {},
            })
        self.assertEqual(tx.state, 'pending')
        with self.assertRaises(ValidationError):
            tx._ompay_validate_redirect_url(
                'https://api.sandbox.truepay.ompay.om@evil.example/api/v1/transactions/x/pay-page',
                '11111111-1111-1111-1111-111111111111',
            )
        for suffix in ('?redirect=https://evil.example', '#fragment'):
            with self.assertRaises(ValidationError):
                tx._ompay_validate_redirect_url(
                    'https://api.sandbox.truepay.ompay.om/api/v1/transactions/'
                    f'11111111-1111-1111-1111-111111111111/pay-page{suffix}',
                    '11111111-1111-1111-1111-111111111111',
                )

    def test_ambiguous_create_recovers_by_reference_without_a_second_create(self):
        tx = self._create_ompay_transaction()
        inquiry_data = self._inquiry_data()
        with patch.object(
            type(tx), '_send_api_request',
            side_effect=[ValidationError('timeout'), self._response(inquiry_data)],
        ) as send_request:
            rendering_values = tx._get_specific_rendering_values({})

        self.assertEqual(send_request.call_count, 2)
        self.assertEqual(send_request.call_args_list[0].args, ('POST', const.BANK_HOSTED_ENDPOINT))
        self.assertEqual(send_request.call_args_list[1].args, ('POST', const.INQUIRY_ENDPOINT))
        self.assertEqual(send_request.call_args_list[1].kwargs['json'], {
            'reference_number': self.reference,
        })
        self.assertIn('/pay-page', rendering_values['api_url'])
        self.assertEqual(tx.provider_reference, inquiry_data['transaction_id'])
        self.assertEqual(tx.state, 'pending')

    def test_ambiguous_create_test_success_marks_done_and_renders_local_status_redirect(self):
        tx = self._create_ompay_transaction()
        with patch.object(
            type(tx), '_send_api_request', side_effect=[
                ValidationError('timeout'), self._response(self._inquiry_data(status='SUCCESSFUL')),
            ]
        ):
            rendering_values = tx._get_specific_rendering_values({})
        self.assertEqual(tx.state, 'done')
        self.assertEqual(rendering_values, {'api_url': '/payment/status', 'url_params': {}})

    def test_unconfirmed_create_stays_pending_for_later_reconciliation(self):
        tx = self._create_ompay_transaction()
        with patch.object(
            type(tx), '_send_api_request', side_effect=[
                ValidationError('create timeout'), ValidationError('inquiry timeout'),
            ]
        ) as send_request:
            rendering_values = tx._get_specific_rendering_values({})
        self.assertEqual(send_request.call_count, 2)
        self.assertTrue(tx.ompay_creation_attempted)
        self.assertFalse(tx.provider_reference)
        self.assertEqual(tx.state, 'pending')
        self.assertEqual(rendering_values, {'api_url': '/payment/status', 'url_params': {}})

    def test_terminal_transaction_never_reopens_ompay_checkout(self):
        tx = self._create_ompay_transaction(
            provider_reference='11111111-1111-1111-1111-111111111111',
            ompay_redirect_url=(
                'https://api.sandbox.truepay.ompay.om/api/v1/transactions/'
                '11111111-1111-1111-1111-111111111111/pay-page'
            ),
        )
        tx._set_done()
        with patch.object(type(tx), '_send_api_request') as send_request:
            rendering_values = tx._get_specific_rendering_values({})
        send_request.assert_not_called()
        self.assertEqual(rendering_values, {'api_url': '/payment/status', 'url_params': {}})

    def test_api_mode_and_payload_validation_fail_before_creation_is_marked(self):
        disabled_tx = self._create_ompay_transaction()
        self.provider.state = 'disabled'
        with patch.object(type(disabled_tx), '_send_api_request') as send_request:
            rendering_values = disabled_tx._get_specific_rendering_values({})
        send_request.assert_not_called()
        self.assertFalse(disabled_tx.ompay_creation_attempted)
        self.assertEqual(rendering_values, {'api_url': '/payment/status', 'url_params': {}})

        self.provider.state = 'enabled'
        cross_environment_tx = self._create_ompay_transaction(
            reference='OMPay-cross-environment-001',
        )
        self.assertTrue(cross_environment_tx.is_live)
        self.provider.state = 'test'
        with patch.object(type(cross_environment_tx), '_send_api_request') as send_request:
            with self.assertRaises(ValidationError):
                cross_environment_tx._ompay_inquire(
                    transaction_id='11111111-1111-1111-1111-111111111111'
                )
        send_request.assert_not_called()

        invalid_currency_tx = self._create_ompay_transaction(
            reference='OMPay-invalid-currency-001', currency_id=self.env.ref('base.USD').id,
        )
        self.assertEqual(invalid_currency_tx._get_specific_rendering_values({}), {
            'api_url': '/payment/status', 'url_params': {},
        })
        self.assertFalse(invalid_currency_tx.ompay_creation_attempted)

    def test_production_return_url_and_amount_precision_are_validated(self):
        tx = self._create_ompay_transaction(is_live=True)
        self.provider.state = 'enabled'
        with patch.object(type(tx), 'get_base_url', return_value='http://shop.example'):
            with self.assertRaises(ValidationError):
                tx._ompay_prepare_payment_request_payload()
        with patch.object(type(tx), 'get_base_url', return_value='https://user:pass@shop.example'):
            with self.assertRaises(ValidationError):
                tx._ompay_prepare_payment_request_payload()

        self.assertEqual(
            tx._extract_amount_data(self._inquiry_data(amount='12.5000'))['amount'], 12.5
        )
        self.assertIsNone(tx._extract_amount_data(self._inquiry_data(amount='12.5004'))['amount'])

        tx.provider_reference = '11111111-1111-1111-1111-111111111111'
        foreign_data = self._inquiry_data(transaction_id='22222222-2222-2222-2222-222222222222')
        self.assertFalse(tx._ompay_is_authoritative_for_transaction(
            foreign_data, allow_missing_provider_reference=True
        ))
        self.assertFalse(tx._ompay_is_valid_return_identifier('valid\x00reference'))
        self.assertFalse(tx._ompay_is_valid_return_identifier('valid\nreference'))

        for invalid_amount in (True, 'NaN', 'Infinity', '-Infinity', object()):
            with self.subTest(invalid_amount=invalid_amount):
                self.assertIsNone(tx._ompay_to_decimal(invalid_amount, round_input=False))

    def test_response_envelope_and_checkout_url_shape_are_strict(self):
        tx = self._create_ompay_transaction()
        for invalid_response in (
            None,
            [],
            {},
            {'success': False, 'data': {}},
            {'success': True, 'data': None},
            {'success': True, 'data': []},
        ):
            with self.subTest(invalid_response=invalid_response):
                with self.assertRaises(ValidationError):
                    tx._ompay_extract_response_data(invalid_response)

        transaction_id = '11111111-1111-1111-1111-111111111111'
        for invalid_url in (
            f'http://api.sandbox.truepay.ompay.om/api/v1/transactions/{transaction_id}/pay-page',
            f'https://api.sandbox.truepay.ompay.om:444/api/v1/transactions/{transaction_id}/pay-page',
            f'https://api.sandbox.truepay.ompay.om/api/v1/transactions/{transaction_id}/otp-page',
        ):
            with self.subTest(invalid_url=invalid_url):
                with self.assertRaises(ValidationError):
                    tx._ompay_validate_redirect_url(invalid_url, transaction_id)

    def test_amount_currency_states_and_idempotence(self):
        tx = self._create_ompay_transaction(
            provider_reference='11111111-1111-1111-1111-111111111111'
        )
        self.assertEqual(tx._extract_amount_data(self._inquiry_data(amount='12.500')), {
            'amount': 12.5,
            'currency_code': 'OMR',
            'precision_digits': 3,
        })
        tx._process('ompay', self._inquiry_data(status='SUCCESSFUL'))
        tx._process('ompay', self._inquiry_data(status='SUCCESSFUL'))
        self.assertEqual(tx.state, 'done')

        self.provider.state = 'enabled'
        live_tx = self._create_ompay_transaction(
            reference='OMPay-live-success',
            provider_reference='22222222-2222-2222-2222-222222222222',
        )
        self.assertTrue(live_tx.is_live)
        live_tx._process('ompay', self._inquiry_data(
            status='SUCCESSFUL',
            transaction_id=live_tx.provider_reference,
            reference_number=live_tx.reference,
        ))
        live_tx._process('ompay', self._inquiry_data(
            status='SUCCESSFUL',
            transaction_id=live_tx.provider_reference,
            reference_number=live_tx.reference,
        ))
        self.assertEqual(live_tx.state, 'done')
        self.provider.state = 'test'

        for status, expected_state in (
            ('PENDING', 'pending'),
            ('PROCESSING', 'pending'),
            ('FAILED', 'error'),
            ('UNKNOWN', 'error'),
        ):
            state_tx = self._create_ompay_transaction(
                reference=f'OMPay-{status}',
                provider_reference='11111111-1111-1111-1111-111111111111',
            )
            state_tx._process(
                'ompay', self._inquiry_data(
                    status=status, reference_number=state_tx.reference
                )
            )
            self.assertEqual(state_tx.state, expected_state)

        invalid_amount_tx = self._create_ompay_transaction(
            reference='OMPay-invalid-amount',
            provider_reference='11111111-1111-1111-1111-111111111111',
        )
        invalid_amount_tx._process(
            'ompay', self._inquiry_data(
                reference_number=invalid_amount_tx.reference, amount='12.501'
            )
        )
        self.assertEqual(invalid_amount_tx.state, 'error')
        invalid_currency_tx = self._create_ompay_transaction(
            reference='OMPay-invalid-currency',
            provider_reference='11111111-1111-1111-1111-111111111111',
        )
        invalid_currency_tx._process(
            'ompay', self._inquiry_data(
                reference_number=invalid_currency_tx.reference, currency='USD'
            )
        )
        self.assertEqual(invalid_currency_tx.state, 'error')

    def test_cron_is_bounded_fair_and_keeps_old_inquiry_failures_pending(self):
        txs = self.env['payment.transaction']
        for index in range(const.RECONCILIATION_BATCH_SIZE + 1):
            txs |= self._create_ompay_transaction(
                reference=f'{self.reference}-cron-{index:02d}',
                ompay_creation_attempted=True,
            )
        txs._set_pending()
        txs.write({
            'last_state_change': fields.Datetime.now() - relativedelta(days=2),
            'ompay_last_return_inquiry_at': fields.Datetime.now() - relativedelta(days=2),
        })

        with patch.object(
            type(txs), '_ompay_inquire', side_effect=ValidationError('timeout')
        ) as inquire, patch.object(
            type(self.env['ir.cron']), '_commit_progress', return_value=60
        ):
            self.env['payment.transaction']._cron_reconcile_ompay_pending_transactions()
            self.assertEqual(inquire.call_count, const.RECONCILIATION_BATCH_SIZE)
            self.assertEqual(len(txs.filtered('ompay_last_reconciliation_at')), 50)

            # The next immediate run must skip the 50 just attempted and select the remaining row.
            self.env['payment.transaction']._cron_reconcile_ompay_pending_transactions()

        self.assertEqual(inquire.call_count, const.RECONCILIATION_BATCH_SIZE + 1)
        self.assertEqual(len(txs.filtered('ompay_last_reconciliation_at')), len(txs))
        self.assertEqual(set(txs.mapped('state')), {'pending'})

    def test_cron_rechecks_state_after_lock(self):
        tx = self._create_ompay_transaction(ompay_creation_attempted=True)
        tx._set_done()
        with patch.object(type(tx), 'search', return_value=tx), patch.object(
            type(tx), '_ompay_inquire'
        ) as inquire:
            self.env['payment.transaction']._cron_reconcile_ompay_pending_transactions()
        inquire.assert_not_called()

    def test_test_cron_recovers_reference_and_marks_success_after_return(self):
        tx = self._create_ompay_transaction(
            ompay_creation_attempted=True,
            ompay_last_return_inquiry_at=fields.Datetime.now() - relativedelta(minutes=10),
        )
        tx._set_pending()
        tx.last_state_change = fields.Datetime.now() - relativedelta(minutes=10)
        inquiry_data = self._inquiry_data(status='SUCCESSFUL')
        with patch.object(type(tx), 'search', return_value=tx), patch.object(
            type(tx), '_ompay_inquire', return_value=inquiry_data
        ) as inquire, patch.object(
            type(self.env['ir.cron']), '_commit_progress', return_value=60
        ):
            self.env['payment.transaction']._cron_reconcile_ompay_pending_transactions()
        inquire.assert_called_once_with(reference_number=tx.reference)
        self.assertEqual(tx.provider_reference, inquiry_data['transaction_id'])
        self.assertEqual(tx.state, 'done')

    def test_cron_isolates_unexpected_failure_and_processes_next_transaction(self):
        first_tx = self._create_ompay_transaction(
            reference=f'{self.reference}-unexpected-1',
            provider_reference='11111111-1111-1111-1111-111111111111',
            ompay_creation_attempted=True,
        )
        second_tx = self._create_ompay_transaction(
            reference=f'{self.reference}-unexpected-2',
            provider_reference='22222222-2222-2222-2222-222222222222',
            ompay_creation_attempted=True,
        )
        txs = first_tx | second_tx
        txs._set_pending()
        txs.write({
            'last_state_change': fields.Datetime.now() - relativedelta(minutes=10),
            'ompay_last_return_inquiry_at': fields.Datetime.now() - relativedelta(minutes=10),
        })
        second_data = self._inquiry_data(
            transaction_id=second_tx.provider_reference,
            reference_number=second_tx.reference,
            status='SUCCESSFUL',
        )

        with patch.object(type(txs), 'search', return_value=txs), patch.object(
            type(txs), '_ompay_inquire', side_effect=[TypeError('unexpected'), second_data]
        ) as inquire, patch.object(
            type(self.env['ir.cron']), '_commit_progress', return_value=60
        ):
            self.env['payment.transaction']._cron_reconcile_ompay_pending_transactions()

        self.assertEqual(inquire.call_count, 2)
        self.assertEqual(first_tx.state, 'pending')
        self.assertEqual(second_tx.state, 'done')
        self.assertTrue(first_tx.ompay_last_reconciliation_at)
        self.assertTrue(second_tx.ompay_last_reconciliation_at)

    def test_cron_does_not_poll_unreturned_test_checkout(self):
        tx = self._create_ompay_transaction(
            provider_reference='11111111-1111-1111-1111-111111111111',
            ompay_creation_attempted=True,
        )
        tx._set_pending()
        tx.last_state_change = fields.Datetime.now() - relativedelta(minutes=10)

        with patch.object(type(tx), '_ompay_inquire') as inquire, patch.object(
            type(self.env['ir.cron']), '_commit_progress', return_value=60
        ):
            self.env['payment.transaction']._cron_reconcile_ompay_pending_transactions()

        inquire.assert_not_called()
        self.assertEqual(tx.state, 'pending')
        self.assertFalse(tx.ompay_last_reconciliation_at)

    def test_cron_can_reconcile_unreturned_live_checkout(self):
        self.provider.state = 'enabled'
        tx = self._create_ompay_transaction(
            provider_reference='11111111-1111-1111-1111-111111111111',
            ompay_creation_attempted=True,
        )
        self.assertTrue(tx.is_live)
        tx._set_pending()
        tx.last_state_change = fields.Datetime.now() - relativedelta(minutes=10)
        inquiry_data = self._inquiry_data(
            transaction_id=tx.provider_reference,
            reference_number=tx.reference,
            status='SUCCESSFUL',
        )

        with patch.object(
            type(tx), '_ompay_inquire', return_value=inquiry_data
        ) as inquire, patch.object(
            type(self.env['ir.cron']), '_commit_progress', return_value=60
        ):
            self.env['payment.transaction']._cron_reconcile_ompay_pending_transactions()

        inquire.assert_called_once_with(transaction_id=tx.provider_reference)
        self.assertEqual(tx.state, 'done')
        self.assertTrue(tx.ompay_last_reconciliation_at)
