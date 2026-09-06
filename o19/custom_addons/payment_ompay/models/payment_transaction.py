# Copyright 2026 Emad. Licensed under LGPL-3.0-or-later.

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib.parse import urlsplit

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import urls

from odoo.addons.payment.logging import get_payment_logger
from odoo.addons.payment_ompay import const
from odoo.addons.payment_ompay.controllers.main import OMPayController


_logger = get_payment_logger(__name__, sensitive_keys=const.SENSITIVE_KEYS)

_PROVIDER_REFERENCE_RE = re.compile(r'^[A-Za-z0-9-]{1,128}$')


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    _ompay_lock_fields = (
        'state',
        'last_state_change',
        'provider_reference',
        'ompay_creation_attempted',
        'ompay_redirect_url',
        'ompay_last_reconciliation_at',
        'ompay_last_return_inquiry_at',
    )

    # These fields keep a render retry from issuing another bank-hosted create request.
    ompay_creation_attempted = fields.Boolean(copy=False, readonly=True)
    ompay_redirect_url = fields.Char(copy=False, readonly=True)
    ompay_last_reconciliation_at = fields.Datetime(copy=False, readonly=True, index=True)
    ompay_last_return_inquiry_at = fields.Datetime(copy=False, readonly=True)

    # === RENDERING METHODS === #

    def _get_specific_rendering_values(self, processing_values):
        """Create one bank-hosted OMPay payment and return its safe GET redirect form values."""
        if self.provider_code != 'ompay':
            return super()._get_specific_rendering_values(processing_values)

        try:
            redirect_url = self._ompay_get_or_create_redirect_url()
        except ValidationError as error:
            if self.ompay_creation_attempted and not self.provider_reference:
                # OMPay might have accepted the request before the response was interrupted.
                # Leave the transaction recoverable; never turn uncertainty into a false failure.
                self._set_pending(state_message=_(
                    'OMPay payment creation is awaiting authenticated confirmation.'
                ))
            elif self.state not in ('done', 'cancel', 'error'):
                self._set_error(str(error))
            # The generic redirect template requires api_url. Never render it without one.
            return self._ompay_local_redirect_values()
        return {'api_url': redirect_url, 'url_params': {}}

    def _ompay_get_or_create_redirect_url(self):
        """Return an existing checkout URL or create exactly one OMPay hosted transaction."""
        self.ensure_one()
        self._ompay_lock_for_creation()
        if self.state in ('done', 'cancel', 'error'):
            return '/payment/status'
        self._ompay_assert_api_mode()
        if self.ompay_redirect_url:
            self._ompay_validate_redirect_url(self.ompay_redirect_url, self.provider_reference)
            return self.ompay_redirect_url

        if self.provider_reference:
            # The transaction was created before a request/render interruption. Inquiry is safe and
            # lets us rebuild only OMPay's canonical public pay-page URL while it remains pending.
            recovered_data = self._ompay_inquire(transaction_id=self.provider_reference)
            if not self._ompay_is_authoritative_for_transaction(recovered_data):
                raise ValidationError(_('OMPay payment verification failed.'))
            self._process('ompay', recovered_data)
            if recovered_data.get('status') not in const.PENDING_STATUSES:
                return '/payment/status'
            return self._ompay_store_canonical_redirect_url(self.provider_reference)

        if self.ompay_creation_attempted:
            # A previous create may have reached OMPay despite an interrupted HTTP response. Do not
            # issue another create; recover by Odoo's unique reference or leave the
            # transaction safe.
            recovered_url = self._ompay_recover_ambiguous_creation()
            if recovered_url:
                return recovered_url
            raise ValidationError(_('OMPay payment creation could not be confirmed.'))

        payload = self._ompay_prepare_payment_request_payload()
        self.write({'ompay_creation_attempted': True})
        try:
            response_content = self._send_api_request(
                'POST', const.BANK_HOSTED_ENDPOINT, json=payload
            )
            response_data = self._ompay_extract_response_data(response_content)
            transaction_id, redirect_url = self._ompay_validate_create_response(response_data)
        except ValidationError:
            recovered_url = self._ompay_recover_ambiguous_creation()
            if recovered_url:
                return recovered_url
            raise

        self.write({
            'provider_reference': transaction_id,
            'ompay_redirect_url': redirect_url,
        })
        self._set_pending()
        return redirect_url

    def _ompay_prepare_payment_request_payload(self):
        """Prepare the documented bank-hosted request without card, wallet, or browser data."""
        self.ensure_one()
        if self.currency_id.name != 'OMR':
            raise ValidationError(_('OMPay supports OMR payments only.'))
        return_url = urls.urljoin(self.get_base_url(), OMPayController._return_url)
        parsed_return_url = urlsplit(return_url)
        if (
            parsed_return_url.scheme not in ('http', 'https')
            or not parsed_return_url.hostname
            or parsed_return_url.username is not None
            or parsed_return_url.password is not None
            or parsed_return_url.query
            or parsed_return_url.fragment
        ):
            raise ValidationError(_('The OMPay return URL must be absolute.'))
        if self.provider_id.state == 'enabled' and parsed_return_url.scheme != 'https':
            raise ValidationError(_('The OMPay production return URL must use HTTPS.'))
        amount = self._ompay_to_decimal(self.amount, round_input=True)
        if amount is None or amount <= 0:
            raise ValidationError(_('The OMPay payment amount is invalid.'))
        return {
            # OMPay requires a JSON number; Decimal avoids an intermediate binary-float calculation.
            'amount': float(amount),
            'currency': self.currency_id.name,
            'return_url': return_url,
            'reference_number': self.reference,
        }

    def _ompay_recover_ambiguous_creation(self):
        """Recover one possibly-created payment by Odoo reference; never retry the create call."""
        self.ensure_one()
        try:
            inquiry_data = self._ompay_inquire(reference_number=self.reference)
        except ValidationError:
            return None
        if not self._ompay_is_authoritative_for_transaction(
            inquiry_data, allow_missing_provider_reference=True
        ):
            return None

        transaction_id = inquiry_data['transaction_id']
        self.provider_reference = transaction_id
        self._process('ompay', inquiry_data)
        if inquiry_data.get('status') not in const.PENDING_STATUSES:
            return '/payment/status'
        return self._ompay_store_canonical_redirect_url(transaction_id)

    def _ompay_store_canonical_redirect_url(self, transaction_id):
        """Build the documented public OMPay pay page after a verified inquiry recovery."""
        self.ensure_one()
        redirect_url = (
            f'{self.provider_id._ompay_get_api_url()}/api/v1/transactions/{transaction_id}/pay-page'
        )
        self._ompay_validate_redirect_url(redirect_url, transaction_id)
        self.ompay_redirect_url = redirect_url
        return redirect_url

    # === PAYMENT DATA METHODS === #

    @api.model
    def _extract_reference(self, provider_code, payment_data):
        if provider_code != 'ompay':
            return super()._extract_reference(provider_code, payment_data)
        return payment_data.get('reference_number') if isinstance(payment_data, dict) else None

    def _extract_amount_data(self, payment_data):
        """Parse OMPay's numeric or string amount for Odoo's standard amount validation."""
        if self.provider_code != 'ompay':
            return super()._extract_amount_data(payment_data)
        payment_data = payment_data if isinstance(payment_data, dict) else {}
        # Do not round an authoritative inquiry amount into equality with the local transaction.
        amount = self._ompay_to_decimal(payment_data.get('amount'), round_input=False)
        return {
            # Odoo's base validator applies its currency-aware comparison before _apply_updates.
            'amount': float(amount) if amount is not None else None,
            'currency_code': payment_data.get('currency'),
            'precision_digits': const.OMR_DECIMAL_PLACES,
        }

    def _apply_updates(self, payment_data):
        if self.provider_code != 'ompay':
            return super()._apply_updates(payment_data)

        if not self._ompay_is_authoritative_for_transaction(payment_data):
            # Keep the local transaction unchanged if a server response does not bind to it.
            raise ValidationError(_('OMPay payment verification failed.'))

        status = payment_data.get('status')
        if status in const.PENDING_STATUSES:
            self._set_pending()
        elif status == const.SUCCESSFUL_STATUS:
            self._set_done()
        elif status == const.FAILED_STATUS:
            self._set_error(_('Your OMPay payment was declined or could not be processed.'))
        else:
            _logger.warning(
                "OMPay returned an invalid status for %(context)s (%(failure)s).",
                {
                    'context': self.provider_id._ompay_log_context(self.reference),
                    'failure': 'invalid_status',
                },
            )
            self._set_error(_('OMPay returned an invalid payment status.'))

    # === OMPAY HELPERS === #

    def _ompay_inquire(self, *, transaction_id=None, reference_number=None):
        """Call the fixed authenticated inquiry endpoint with exactly one server-side identifier."""
        self.ensure_one()
        self._ompay_assert_api_mode()
        if bool(transaction_id) == bool(reference_number):
            raise ValidationError(_('OMPay inquiry requires exactly one identifier.'))
        payload = {'transaction_id': transaction_id} if transaction_id else {
            'reference_number': reference_number,
        }
        response_content = self._send_api_request(
            'POST', const.INQUIRY_ENDPOINT, json=payload
        )
        return self._ompay_extract_response_data(response_content)

    def _ompay_extract_response_data(self, response_content):
        """Require OMPay's documented `{success: true, data: {...}}` response envelope."""
        if (
            not isinstance(response_content, dict)
            or response_content.get('success') is not True
            or not isinstance(response_content.get('data'), dict)
        ):
            raise ValidationError(_('OMPay returned an invalid response.'))
        return response_content['data']

    def _ompay_validate_create_response(self, response_data):
        """Validate every value that can influence the browser redirect before storing it."""
        status = response_data.get('status')
        transaction_id = response_data.get('transaction_id')
        redirect_url = response_data.get('redirect_url')
        if status not in const.PENDING_STATUSES:
            raise ValidationError(_('OMPay did not start a hosted payment.'))
        if not self._ompay_is_valid_provider_reference(transaction_id):
            raise ValidationError(_('OMPay returned an invalid transaction identifier.'))
        self._ompay_validate_redirect_url(redirect_url, transaction_id)
        return transaction_id, redirect_url

    def _ompay_validate_redirect_url(self, redirect_url, transaction_id):
        """Reject redirects that are not OMPay's exact HTTPS pay-page URL for this transaction."""
        if not isinstance(redirect_url, str) or not self._ompay_is_valid_provider_reference(
            transaction_id
        ):
            raise ValidationError(_('OMPay returned an invalid checkout URL.'))
        try:
            parsed_url = urlsplit(redirect_url)
            expected_url = urlsplit(self.provider_id._ompay_get_api_url())
            port = parsed_url.port
        except ValueError:
            raise ValidationError(_('OMPay returned an invalid checkout URL.')) from None
        expected_path = f'/api/v1/transactions/{transaction_id}/pay-page'
        if (
            parsed_url.scheme.lower() != 'https'
            or parsed_url.username is not None
            or parsed_url.password is not None
            or parsed_url.hostname != expected_url.hostname
            or port not in (None, 443)
            or parsed_url.path != expected_path
            or parsed_url.query
            or parsed_url.fragment
        ):
            raise ValidationError(_('OMPay returned an invalid checkout URL.'))

    def _ompay_is_authoritative_for_transaction(
        self, payment_data, *, allow_missing_provider_reference=False
    ):
        """Check that an inquiry result identifies this local transaction before it is processed."""
        self.ensure_one()
        if not isinstance(payment_data, dict):
            return False
        transaction_id = payment_data.get('transaction_id')
        if not self._ompay_is_valid_provider_reference(transaction_id):
            return False
        if payment_data.get('reference_number') != self.reference:
            return False
        return (
            allow_missing_provider_reference
            and not self.provider_reference
        ) or transaction_id == self.provider_reference

    @staticmethod
    def _ompay_is_valid_provider_reference(value):
        return isinstance(value, str) and bool(_PROVIDER_REFERENCE_RE.fullmatch(value))

    @staticmethod
    def _ompay_is_valid_return_identifier(value):
        # Odoo references are generated server-side but may contain normal document punctuation.
        return (
            isinstance(value, str)
            and 0 < len(value) <= 255
            and not any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)
        )

    @staticmethod
    def _ompay_to_decimal(value, *, round_input):
        """Parse and round OMR without comparing binary float values."""
        if isinstance(value, bool):
            return None
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None
        if not amount.is_finite():
            return None
        try:
            rounded_amount = amount.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError):
            return None
        if not round_input and amount != rounded_amount:
            return None
        return rounded_amount

    def _ompay_assert_api_mode(self):
        """Prevent disabled requests and transactions that cross OMPay environments."""
        self.ensure_one()
        if self.provider_id.state == 'disabled':
            raise ValidationError(_('OMPay is disabled.'))
        expected_is_live = self.provider_id.state == 'enabled'
        if self.is_live != expected_is_live:
            raise ValidationError(_(
                'The OMPay transaction environment does not match the provider.'
            ))
        self.provider_id._ompay_validate_api_credentials()

    def _ompay_lock_for_creation(self):
        """Serialize checkout rendering so concurrent requests cannot create duplicate payments."""
        self.ensure_one()
        self.flush_recordset(self._ompay_lock_fields)
        self.env.cr.execute(
            'SELECT id FROM payment_transaction WHERE id = %s FOR UPDATE', [self.id]
        )
        self.invalidate_recordset(self._ompay_lock_fields)

    @staticmethod
    def _ompay_local_redirect_values():
        """Return rendering values that keep failed or terminal flows inside Odoo."""
        return {'api_url': '/payment/status', 'url_params': {}}

    # === CRON METHODS === #

    @api.model
    def _cron_reconcile_ompay_pending_transactions(self):
        """Bounded recovery for returns the customer never completes in the browser."""
        now = fields.Datetime.now()
        domain = [
            ('provider_code', '=', 'ompay'),
            ('state', '=', 'pending'),
            ('ompay_creation_attempted', '=', True),
            (
                'last_state_change',
                '<=',
                now - relativedelta(minutes=const.RECONCILIATION_MIN_AGE_MINUTES),
            ),
            # The TruePay sandbox has returned SUCCESSFUL for untouched and incomplete hosted
            # checkouts. Fail closed there: only retry an inquiry after the browser reached Odoo's
            # return route. Live transactions retain documented unattended reconciliation.
            '|',
            ('is_live', '=', True),
            ('ompay_last_return_inquiry_at', '!=', False),
            '|',
            ('ompay_last_reconciliation_at', '=', False),
            (
                'ompay_last_reconciliation_at',
                '<=',
                now - relativedelta(minutes=const.RECONCILIATION_COOLDOWN_MINUTES),
            ),
        ]
        txs = self.search(
            domain,
            order='ompay_last_reconciliation_at asc nulls first, create_date asc',
            limit=const.RECONCILIATION_BATCH_SIZE,
        )
        cron = self.env['ir.cron']
        for candidate in txs:
            # Reuse Odoo's non-blocking row lock and re-check the due domain after acquiring it.
            # This serializes reconciliation with the hosted-return controller without making a
            # cron worker wait behind an in-flight return.
            tx = candidate.try_lock_for_update()
            if not tx:
                continue
            # Recordsets returned by the initial search share a prefetch set. Restrict it and
            # invalidate every decision field after the lock so a prior callback commit cannot be
            # hidden by values cached while processing another candidate.
            tx = tx.with_prefetch()
            tx.invalidate_recordset(self._ompay_lock_fields)
            tx = tx.filtered_domain(domain)
            if not tx:
                continue
            tx.ompay_last_reconciliation_at = fields.Datetime.now()
            failure = None
            try:
                # A savepoint keeps one malformed record or unexpected parser defect from aborting
                # the remaining reconciliation batch. The attempt timestamp is deliberately set
                # before the savepoint so a repeatedly bad row cannot starve newer transactions.
                with self.env.cr.savepoint():
                    if tx.provider_reference:
                        inquiry_data = tx._ompay_inquire(transaction_id=tx.provider_reference)
                        is_authoritative = tx._ompay_is_authoritative_for_transaction(inquiry_data)
                    else:
                        inquiry_data = tx._ompay_inquire(reference_number=tx.reference)
                        is_authoritative = tx._ompay_is_authoritative_for_transaction(
                            inquiry_data, allow_missing_provider_reference=True
                        )
                    if not is_authoritative:
                        raise ValidationError(_('OMPay payment verification failed.'))
                    if not tx.provider_reference:
                        tx.provider_reference = inquiry_data['transaction_id']
                    tx._process('ompay', inquiry_data)
            except ValidationError:
                failure = 'inquiry_failed'
            except Exception:
                # Do not include exception text: a third-party parser or transport exception can
                # carry response data. Continue safely and leave the transaction pending.
                failure = 'unexpected_error'

            if failure:
                _logger.warning(
                    "OMPay reconciliation failed for %(context)s (%(failure)s).",
                    {
                        'context': tx.provider_id._ompay_log_context(tx.reference),
                        'failure': failure,
                    },
                )
            if not cron._commit_progress(1):
                break
