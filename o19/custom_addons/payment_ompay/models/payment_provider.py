# Copyright 2026 Emad. Licensed under LGPL-3.0-or-later.

import re

import requests
from requests.auth import AuthBase

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment.logging import get_payment_logger
from odoo.addons.payment_ompay import const


_logger = get_payment_logger(__name__, sensitive_keys=const.SENSITIVE_KEYS)


class _OMPayHeaderAuth(AuthBase):
    """Attach OMPay credentials only to the initial, allowlisted API request."""

    def __init__(self, api_key, api_secret):
        self._api_key = api_key
        self._api_secret = api_secret

    def __call__(self, prepared_request):
        prepared_request.headers['OMPAY-API-Key'] = self._api_key
        prepared_request.headers['OMPAY-API-Secret'] = self._api_secret
        prepared_request.register_hook('response', self._reject_redirect)
        return prepared_request

    @staticmethod
    def _reject_redirect(response, *args, **kwargs):
        """Fail before Requests can forward custom credential headers to a redirect target."""
        if 300 <= response.status_code < 400:
            raise requests.exceptions.ConnectionError('OMPay API redirects are not allowed.')
        return response


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('ompay', 'OMPay')], ondelete={'ompay': 'set default'}
    )
    ompay_api_key = fields.Char(
        string='OMPay API Key',
        required_if_provider='ompay',
        copy=False,
        groups='base.group_system',
    )
    ompay_api_secret = fields.Char(
        string='OMPay API Secret',
        required_if_provider='ompay',
        copy=False,
        groups='base.group_system',
    )

    # === COMPUTE METHODS === #

    def _compute_feature_support_fields(self):
        """OMPay is deliberately limited to one hosted, redirect payment flow."""
        super()._compute_feature_support_fields()
        self.filtered(lambda provider: provider.code == 'ompay').update({
            'support_tokenization': False,
            'support_manual_capture': None,
            'support_express_checkout': False,
            'support_refund': 'none',
        })

    def _get_supported_currencies(self):
        """Return OMR only, until another OMPay currency is explicitly supported."""
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'ompay':
            supported_currencies = supported_currencies.filtered(
                lambda currency: currency.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    # === CRUD METHODS === #

    def _get_default_payment_method_codes(self):
        self.ensure_one()
        if self.code != 'ompay':
            return super()._get_default_payment_method_codes()
        return const.DEFAULT_PAYMENT_METHOD_CODES

    def _get_reset_values(self):
        reset_values = super()._get_reset_values()
        if self.code == 'ompay':
            reset_values.update({
                'ompay_api_key': None,
                'ompay_api_secret': None,
            })
        return reset_values

    @api.constrains('code', 'ompay_api_key', 'ompay_api_secret')
    def _check_ompay_credentials(self):
        """Keep credentials safe for use as HTTP header values."""
        for provider in self.filtered(lambda candidate: candidate.code == 'ompay'):
            for credential in (provider.ompay_api_key, provider.ompay_api_secret):
                contains_invalid_character = credential and any(
                    not 0x21 <= ord(character) <= 0x7E for character in credential
                )
                if contains_invalid_character:
                    raise ValidationError(_(
                        'OMPay credentials must contain printable ASCII characters without spaces.'
                    ))

    # === REQUEST HELPERS === #

    def _send_api_request(
        self, method, endpoint, *, params=None, data=None, json=None, reference=None, **kwargs
    ):
        """Normalize every Requests failure into Odoo's payment error contract."""
        if self.code != 'ompay':
            return super()._send_api_request(
                method,
                endpoint,
                params=params,
                data=data,
                json=json,
                reference=reference,
                **kwargs,
            )
        try:
            return super()._send_api_request(
                method,
                endpoint,
                params=params,
                data=data,
                json=json,
                reference=reference,
                **kwargs,
            )
        except ValidationError:
            raise
        except requests.exceptions.RequestException:
            # Odoo already normalizes connection errors and timeouts. This catches less common
            # transport failures such as truncated/chunked responses without exposing details.
            raise ValidationError(_(
                'Could not establish the connection to the payment provider.'
            )) from None

    def _ompay_get_api_url(self):
        """Return the immutable API origin for the provider's standard Odoo state."""
        self.ensure_one()
        # A disabled provider cannot send a request; keeping it on sandbox avoids a mutable host.
        environment = 'enabled' if self.state == 'enabled' else 'test'
        return const.API_URLS[environment]

    def _build_request_url(self, endpoint, **kwargs):
        """Allow only the two documented /api/v1 server-to-server endpoints."""
        if self.code != 'ompay':
            return super()._build_request_url(endpoint, **kwargs)
        if endpoint not in const.ALLOWED_ENDPOINTS:
            raise ValidationError(_('Unsupported OMPay API endpoint.'))
        return f'{self._ompay_get_api_url()}{endpoint}'

    def _build_request_headers(self, *args, **kwargs):
        if self.code != 'ompay':
            return super()._build_request_headers(*args, **kwargs)
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def _build_request_auth(self, **kwargs):
        """Use Requests auth so credential headers can reject redirects before they are followed."""
        if self.code != 'ompay':
            return super()._build_request_auth(**kwargs)
        self.ensure_one()
        self._ompay_validate_api_credentials()
        return _OMPayHeaderAuth(self.ompay_api_key, self.ompay_api_secret)

    def _parse_response_content(self, response, **kwargs):
        """Reject malformed successful responses with a sanitized Odoo payment error."""
        if self.code != 'ompay':
            return super()._parse_response_content(response, **kwargs)
        try:
            response_content = response.json()
        except (requests.exceptions.RequestException, TypeError, ValueError):
            raise ValidationError(_('OMPay returned an invalid response.')) from None
        if not isinstance(response_content, dict):
            raise ValidationError(_('OMPay returned an invalid response.'))
        return response_content

    def _log_request(self, method, url, payload, *, reference=None):
        """Log request metadata without URLs, payloads, or credentials."""
        if self.code != 'ompay':
            return super()._log_request(method, url, payload, reference=reference)
        context = self._ompay_log_context(reference)
        _logger.info(
            "Sending %(method)s OMPay API request for %(context)s.",
            {'method': method, 'context': context},
        )

    def _log_response(self, response, *, reference=None):
        """Log only the status code; provider bodies can contain sensitive diagnostics."""
        if self.code != 'ompay':
            return super()._log_response(response, reference=reference)
        log_method = _logger.info if response.ok else _logger.error
        log_method(
            "Received HTTP %(code)s OMPay API response for %(context)s.",
            {'code': response.status_code, 'context': self._ompay_log_context(reference)},
        )

    def _parse_response_error(self, response):
        """Expose a stable error code, never OMPay's raw response text or request payload."""
        if self.code != 'ompay':
            return super()._parse_response_error(response)

        error_data = {}
        try:
            parsed_data = response.json()
            if isinstance(parsed_data, dict):
                error_data = parsed_data
        except (AttributeError, TypeError, ValueError):
            pass

        error_code = self._ompay_sanitize_identifier(
            error_data.get('error'), fallback='REQUEST_FAILED'
        )
        request_id = self._ompay_sanitize_identifier(error_data.get('requestId'), fallback=None)
        identifier = error_code if not request_id else f'{error_code}; request {request_id}'
        return _('OMPay request failed (%(identifier)s).', identifier=identifier)

    @staticmethod
    def _ompay_sanitize_identifier(value, fallback):
        """Keep provider error metadata safe enough for a user-facing support reference."""
        if not isinstance(value, str):
            return fallback
        identifier = re.sub(r'[^A-Za-z0-9_.-]', '', value)[:128]
        return identifier or fallback

    def _ompay_log_context(self, reference):
        """Return a bounded, single-line local identifier for diagnostic logs."""
        if not isinstance(reference, str):
            return f'provider {self.id}'
        safe_reference = re.sub(r'[\x00-\x1f\x7f]', '_', reference)[:128]
        return f'transaction {safe_reference}'

    def _ompay_validate_api_credentials(self):
        """Fail locally before any request is marked as attempted."""
        self.ensure_one()
        if not self.ompay_api_key or not self.ompay_api_secret:
            raise ValidationError(_('The OMPay API credentials are missing.'))
