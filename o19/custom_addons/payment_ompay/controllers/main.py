# Copyright 2026 Emad. Licensed under LGPL-3.0-or-later.

from datetime import timedelta

from werkzeug.exceptions import Forbidden

from odoo import fields, http
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.payment.logging import get_payment_logger
from odoo.addons.payment_ompay import const


_logger = get_payment_logger(__name__, sensitive_keys=const.SENSITIVE_KEYS)


class OMPayController(http.Controller):
    """Routes used only after OMPay's hosted checkout redirects the cardholder back."""

    _return_url = '/payment/ompay/return'

    @http.route(
        _return_url,
        type='http',
        auth='public',
        methods=['GET'],
        save_session=False,
    )
    def ompay_return_from_checkout(self, reference_number=None, transaction_id=None, **_kwargs):
        """Verify identifiers, then use authenticated inquiry as the sole status authority."""
        transaction_model = request.env['payment.transaction'].sudo()
        if not transaction_model._ompay_is_valid_return_identifier(reference_number):
            raise Forbidden()
        if not transaction_model._ompay_is_valid_provider_reference(transaction_id):
            raise Forbidden()

        tx_sudo = transaction_model.search([
            ('provider_code', '=', 'ompay'),
            ('reference', '=', reference_number),
        ], limit=2)
        if len(tx_sudo) != 1:
            raise Forbidden()

        tx_sudo._ompay_lock_for_creation()
        if tx_sudo.provider_reference:
            if tx_sudo.provider_reference != transaction_id:
                raise Forbidden()
            inquiry_identifier = {'transaction_id': transaction_id}
            allow_missing_provider_reference = False
        elif tx_sudo.ompay_creation_attempted and tx_sudo.state == 'pending':
            # The create response may have been lost. Recover by the server-generated Odoo
            # reference, but require OMPay's result to match the browser's transaction id.
            inquiry_identifier = {'reference_number': tx_sudo.reference}
            allow_missing_provider_reference = True
        else:
            raise Forbidden()

        # Replayed returns must not trigger more provider calls after Odoo reached a terminal state.
        if tx_sudo.state in ('done', 'cancel', 'error'):
            return self._redirect_to_status()

        now = fields.Datetime.now()
        cooldown_start = now - timedelta(seconds=const.RETURN_INQUIRY_COOLDOWN_SECONDS)
        if (
            tx_sudo.ompay_last_return_inquiry_at
            and tx_sudo.ompay_last_return_inquiry_at >= cooldown_start
        ):
            return self._redirect_to_status()
        tx_sudo.ompay_last_return_inquiry_at = now

        try:
            inquiry_data = tx_sudo._ompay_inquire(**inquiry_identifier)
        except ValidationError:
            # The transaction remains pending. The bounded reconciliation cron will retry safely.
            _logger.warning(
                "OMPay inquiry failed after hosted return for %(context)s "
                "(%(failure)s).",
                {
                    'context': tx_sudo.provider_id._ompay_log_context(tx_sudo.reference),
                    'failure': 'inquiry_failed',
                },
            )
        else:
            if (
                inquiry_data.get('transaction_id') != transaction_id
                or not tx_sudo._ompay_is_authoritative_for_transaction(
                    inquiry_data,
                    allow_missing_provider_reference=allow_missing_provider_reference,
                )
            ):
                raise Forbidden()
            if not tx_sudo.provider_reference:
                tx_sudo.provider_reference = transaction_id
            tx_sudo._process('ompay', inquiry_data)

        return self._redirect_to_status()

    @staticmethod
    def _redirect_to_status():
        """Keep callback identifiers out of caches and the next request's Referer header."""
        response = request.redirect('/payment/status')
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response
