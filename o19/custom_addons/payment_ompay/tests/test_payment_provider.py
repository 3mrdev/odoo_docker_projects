# Copyright 2026 Emad. Licensed under LGPL-3.0-or-later.

import logging
from types import SimpleNamespace
from unittest.mock import patch, sentinel

import requests

from odoo.exceptions import ValidationError

from odoo.addons.payment.models.payment_provider import PaymentProvider as BasePaymentProvider
from odoo.addons.payment_ompay import const
from odoo.addons.payment_ompay.models.payment_provider import _logger
from odoo.addons.payment_ompay.tests.common import OMPayCommon


class TestOMPayProvider(OMPayCommon):

    def test_reset_values_preserve_inherited_fields_and_clear_ompay_credentials(self):
        with patch.object(
            BasePaymentProvider,
            '_get_reset_values',
            return_value={'inherited_credential': None},
        ) as base_reset:
            reset_values = self.provider._get_reset_values()

        base_reset.assert_called_once_with()
        self.assertEqual(reset_values, {
            'inherited_credential': None,
            'ompay_api_key': None,
            'ompay_api_secret': None,
        })

    def test_send_api_request_delegates_non_ompay_provider_to_payment_base(self):
        other_provider = self.env['payment.provider'].new({'code': 'none'})
        with patch.object(
            BasePaymentProvider, '_send_api_request', return_value=sentinel.response
        ) as base_send:
            response = other_provider._send_api_request(
                'POST',
                '/base-provider-endpoint',
                params={'query': 'value'},
                data=b'raw-data',
                json={'amount': 12.5},
                reference='BASE-REQUEST-001',
                provider_option=True,
            )

        self.assertIs(response, sentinel.response)
        base_send.assert_called_once_with(
            'POST',
            '/base-provider-endpoint',
            params={'query': 'value'},
            data=b'raw-data',
            json={'amount': 12.5},
            reference='BASE-REQUEST-001',
            provider_option=True,
        )

    def test_environment_urls_headers_currency_and_features(self):
        self.provider.state = 'test'
        self.assertEqual(
            self.provider._build_request_url(const.BANK_HOSTED_ENDPOINT),
            'https://api.sandbox.truepay.ompay.om/api/v1/transactions/bank-hosted',
        )
        self.provider.state = 'enabled'
        self.assertEqual(
            self.provider._build_request_url(const.INQUIRY_ENDPOINT),
            'https://api.truepay.ompay.om/api/v1/transactions/inquiry',
        )
        self.assertEqual(self.provider._build_request_headers(), {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })
        prepared_request = requests.Request(
            'POST',
            self.provider._build_request_url(const.INQUIRY_ENDPOINT),
            auth=self.provider._build_request_auth(),
        ).prepare()
        self.assertEqual(prepared_request.headers['OMPAY-API-Key'], 'ompay-test-api-key')
        self.assertEqual(prepared_request.headers['OMPAY-API-Secret'], 'ompay-test-api-secret')
        redirect_response = requests.Response()
        redirect_response.status_code = 302
        with self.assertRaises(requests.exceptions.ConnectionError):
            prepared_request.hooks['response'][0](redirect_response)
        self.assertEqual(self.provider._get_default_payment_method_codes(), {'card'})
        self.assertEqual(self.provider._get_supported_currencies(), self.currency)
        self.assertFalse(self.provider.support_tokenization)
        self.assertFalse(self.provider.support_express_checkout)
        self.assertEqual(self.provider.support_refund, 'none')

    def test_only_documented_api_endpoints_and_sanitized_errors(self):
        with self.assertRaises(ValidationError):
            self.provider._build_request_url('/api/v1/transactions/merchant-hosted')

        class Response:
            @staticmethod
            def json():
                return {
                    'error': 'INVALID_CREDENTIALS',
                    'message': 'ompay-test-api-secret must never appear',
                    'requestId': 'req-123',
                }

        error_message = self.provider._parse_response_error(Response())
        self.assertIn('INVALID_CREDENTIALS', error_message)
        self.assertIn('req-123', error_message)
        self.assertNotIn('ompay-test-api-secret', error_message)

    def test_payment_logger_masks_ompay_credentials(self):
        secret = 'ompay-test-api-secret'
        record = logging.LogRecord(
            _logger.name,
            logging.INFO,
            __file__,
            0,
            'Diagnostic values: %s',
            ({'OMPAY-API-Secret': secret},),
            None,
        )
        for log_filter in _logger.filters:
            log_filter.filter(record)
        self.assertNotIn(secret, str(record.args))
        self.assertIn('[REDACTED]', str(record.args))

    def test_request_and_response_logs_omit_payloads_urls_and_response_bodies(self):
        secret = 'a-provider-secret-that-must-not-be-logged'
        with patch.object(_logger, 'info') as log_info:
            self.provider._log_request(
                'POST', f'https://api.example/{secret}', {'secret': secret},
                reference='OMPay-TEST\nINJECTED',
            )
        self.assertNotIn(secret, str(log_info.call_args))
        self.assertNotIn('api.example', str(log_info.call_args))
        self.assertIn('OMPay-TEST_INJECTED', str(log_info.call_args))

        response = SimpleNamespace(
            ok=False,
            status_code=400,
            reason=secret,
            text=secret,
            url=f'https://api.example/{secret}',
        )
        with patch.object(_logger, 'error') as log_error:
            self.provider._log_response(response, reference=self.reference)
        self.assertNotIn(secret, str(log_error.call_args))
        self.assertNotIn('api.example', str(log_error.call_args))

    def test_malformed_and_truncated_responses_become_sanitized_validation_errors(self):
        malformed_response = requests.Response()
        malformed_response.status_code = 200
        malformed_response.url = self.provider._build_request_url(const.INQUIRY_ENDPOINT)
        malformed_response._content = b'not-json-and-not-safe-to-display'

        with patch.object(requests, 'request', return_value=malformed_response):
            with self.assertRaisesRegex(ValidationError, 'invalid response') as error:
                self.provider._send_api_request(
                    'POST', const.INQUIRY_ENDPOINT, json={'transaction_id': 'safe-id'}
                )
        self.assertNotIn('not-safe-to-display', str(error.exception))

        with patch.object(
            requests,
            'request',
            side_effect=requests.exceptions.ChunkedEncodingError('sensitive transport detail'),
        ):
            with self.assertRaises(ValidationError) as error:
                self.provider._send_api_request(
                    'POST', const.INQUIRY_ENDPOINT, json={'transaction_id': 'safe-id'}
                )
        self.assertNotIn('sensitive transport detail', str(error.exception))

    def test_http_error_responses_are_sanitized(self):
        unsafe_text = 'raw-provider-body-with-ompay-test-api-secret'
        for status_code, content in (
            (401, b'{"error":"INVALID_CREDENTIALS","message":"' + unsafe_text.encode() + b'"}'),
            (403, b'{"error":"FORBIDDEN","message":"' + unsafe_text.encode() + b'"}'),
            (409, b'{"error":"DUPLICATE_ENTRY","message":"' + unsafe_text.encode() + b'"}'),
            (429, b'{"error":"RATE_LIMITED","message":"' + unsafe_text.encode() + b'"}'),
            (500, unsafe_text.encode()),
        ):
            with self.subTest(status_code=status_code):
                response = requests.Response()
                response.status_code = status_code
                response.url = self.provider._build_request_url(const.INQUIRY_ENDPOINT)
                response._content = content
                with patch.object(requests, 'request', return_value=response):
                    with self.assertRaises(ValidationError) as error:
                        self.provider._send_api_request(
                            'POST', const.INQUIRY_ENDPOINT, json={'transaction_id': 'safe-id'}
                        )
                self.assertNotIn(unsafe_text, str(error.exception))
                self.assertNotIn('ompay-test-api-secret', str(error.exception))

    def test_credentials_reject_whitespace_control_characters_and_non_ascii(self):
        for invalid_value in (' leading-space', 'line\nbreak', 'non-ascii-\u0661'):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.provider.ompay_api_secret = invalid_value
