# -*- coding: utf-8 -*-

from datetime import timedelta
import urllib.parse

from psycopg2.errors import LockNotAvailable

from odoo import _, http
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.fields import Command
from odoo.http import request
from odoo.tools import SQL

from odoo.addons.payment.controllers import portal as payment_portal
from odoo.addons.sale.controllers import portal as sale_portal

from .common import LogspaceController


class LogspacePaymentController(LogspaceController, payment_portal.PaymentPortal):
    """Provider-neutral payment flow for Logspace sale orders."""

    DRAFT_RETRY_AFTER = timedelta(minutes=30)

    @staticmethod
    def _secure_response(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    @staticmethod
    def _payment_url(order, access_token):
        query = urllib.parse.urlencode({'access_token': access_token})
        return f'/logspace/booking/payment/{order.id}?{query}'

    @staticmethod
    def _result_url(order, access_token):
        query = urllib.parse.urlencode({'access_token': access_token})
        return f'/logspace/booking/payment/result/{order.id}?{query}'

    @staticmethod
    def _track_url(order, access_token):
        """Logspace order view (pickup/dropoff, status, payment) instead of /my/orders."""
        query = urllib.parse.urlencode({'access_token': access_token})
        return f'/logspace/my/orders/track/{order.name}?{query}'

    def _check_logspace_order_access(self, order_id, access_token):
        try:
            order_sudo = self._document_check_access(
                'sale.order', order_id, access_token=access_token,
            )
        except (AccessError, MissingError) as error:
            raise MissingError(_("The Logspace order could not be found.")) from error
        if not order_sudo.is_logspace_order:
            raise MissingError(_("The Logspace order could not be found."))
        return order_sudo

    @http.route(
        '/logspace/booking/payment', type='http', methods=['GET'], auth='public', website=True,
        sitemap=False,
    )
    def logspace_payment_entry(self, **_kwargs):
        """Turn the server-side booking session into a token-protected payment URL."""
        order_id = request.session.get('logspace_order_id')
        order_sudo = request.env['sale.order'].sudo().browse(order_id).exists()
        if (
            not order_sudo
            or not order_sudo.is_logspace_order
            or order_sudo.state not in ('draft', 'sent')
        ):
            request.session.pop('logspace_order_id', None)
            return request.redirect('/logspace/booking/details')
        return request.redirect(
            self._payment_url(order_sudo, order_sudo._portal_ensure_token())
        )

    @http.route(
        '/logspace/booking/payment/<int:order_id>', type='http', methods=['GET'], auth='public',
        website=True, sitemap=False,
    )
    def logspace_payment(self, order_id, access_token=None, **_kwargs):
        """Display Odoo's standard payment form for an authoritative Logspace sale order."""
        try:
            order_sudo = self._check_logspace_order_access(order_id, access_token)
        except MissingError:
            return request.redirect('/logspace/booking/details')

        if order_sudo.state not in ('draft', 'sent') or not order_sudo.order_line:
            return request.redirect(
                self._result_url(order_sudo, order_sudo._portal_ensure_token())
            )
        if order_sudo.currency_id.compare_amounts(order_sudo.amount_total, 0) <= 0:
            raise ValidationError(_("This order does not have a positive amount to pay."))
        if order_sudo._get_blocking_logspace_transactions(self.DRAFT_RETRY_AFTER):
            return request.redirect(
                self._result_url(order_sudo, order_sudo._portal_ensure_token())
            )

        payment_values = sale_portal.CustomerPortal._get_payment_values(
            self, order_sudo, website_id=request.website.id,
        )
        order_access_token = payment_values['access_token']
        is_public = request.env.user._is_public()
        if is_public:
            payment_values.update({
                'tokens_sudo': request.env['payment.token'].sudo().browse(),
                'allow_token_selection': False,
                'show_tokenize_input_mapping': {
                    provider.id: False for provider in payment_values['providers_sudo']
                },
            })

        payment_values.update({
            'transaction_route': f'/logspace/booking/payment/transaction/{order_sudo.id}',
            'landing_route': self._result_url(order_sudo, order_access_token),
            'sale_order_id': order_sudo.id,
            'display_submit_button': True,
            'submit_button_label': _("Pay now"),
            'order': order_sudo,
            'total': order_sudo.amount_total,
            'subtotal': order_sudo.amount_untaxed,
            'tax': order_sudo.amount_tax,
            'current_step': 4,
            'total_steps': 4,
            'steps': ['Details', 'Add-ons', 'Checkout', 'Payment'],
            'booking_data': request.session.get('logspace_booking') or {},
            'is_public_payment': is_public,
        })
        return self._secure_response(
            request.render(
                'appness_logspace.logspace_payment_page',
                self._get_page_context(payment_values),
            )
        )

    @http.route(
        '/logspace/booking/payment/transaction/<int:order_id>',
        type='jsonrpc', auth='public', website=True,
    )
    def logspace_payment_transaction(self, order_id, access_token, **kwargs):
        """Create a standard transaction after validating and locking the Logspace order."""
        order_sudo = self._check_logspace_order_access(order_id, access_token)
        try:
            with request.env.cr.savepoint():
                request.env.cr.execute(SQL(
                    'SELECT 1 FROM sale_order WHERE id = %s FOR NO KEY UPDATE NOWAIT', order_id,
                ))
        except LockNotAvailable as error:
            raise UserError(_("Payment is already being processed.")) from error

        order_sudo.invalidate_recordset()
        if order_sudo.state == 'cancel':
            raise ValidationError(_("The order has been cancelled."))
        if order_sudo.state not in ('draft', 'sent') or not order_sudo.order_line:
            raise ValidationError(_("This order is not ready to be paid."))

        self._validate_transaction_kwargs(kwargs)
        if kwargs.get('is_validation'):
            raise ValidationError(_("Validation transactions are not allowed for Logspace orders."))

        amount = self._cast_as_float(kwargs.get('amount'))
        if amount is None or order_sudo.currency_id.compare_amounts(
            amount, order_sudo.amount_total,
        ):
            raise ValidationError(_("The order total changed. Please refresh the payment page."))
        if order_sudo.currency_id.compare_amounts(order_sudo.amount_total, 0) <= 0:
            raise ValidationError(_("This order does not have a positive amount to pay."))
        if order_sudo.currency_id.compare_amounts(
            order_sudo.amount_paid, order_sudo.amount_total,
        ) >= 0:
            raise UserError(_("The order has already been paid."))
        if order_sudo._get_blocking_logspace_transactions(self.DRAFT_RETRY_AFTER):
            raise UserError(_("A payment is already being processed for this order."))

        logged_in = not request.env.user._is_public()
        partner_sudo = (
            request.env.user.partner_id if logged_in else order_sudo.partner_id
        )
        if not self._can_partner_pay_in_company(partner_sudo, order_sudo.company_id):
            raise ValidationError(_("The customer cannot pay in the order's company."))

        provider_id = self._cast_as_int(kwargs.get('provider_id'))
        payment_method_id = self._cast_as_int(kwargs.get('payment_method_id'))
        token_id = self._cast_as_int(kwargs.get('token_id'))
        flow = kwargs.get('flow')
        if flow not in ('redirect', 'direct', 'token'):
            raise ValidationError(_("The selected payment flow is invalid."))

        availability_report = {}
        providers_sudo = request.env['payment.provider'].sudo()._get_compatible_providers(
            order_sudo.company_id.id,
            partner_sudo.id,
            order_sudo.amount_total,
            currency_id=order_sudo.currency_id.id,
            sale_order_id=order_sudo.id,
            website_id=request.website.id,
            report=availability_report,
        )
        provider_sudo = providers_sudo.filtered(lambda provider: provider.id == provider_id)
        if not provider_sudo:
            raise ValidationError(_("The selected payment provider is not available for this order."))

        payment_methods_sudo = request.env[
            'payment.method'
        ].sudo()._get_compatible_payment_methods(
            providers_sudo.ids,
            partner_sudo.id,
            currency_id=order_sudo.currency_id.id,
            sale_order_id=order_sudo.id,
            website_id=request.website.id,
            report=availability_report,
        )
        if flow == 'token':
            if not logged_in or not token_id:
                raise AccessError(_("Saved payment methods require an authenticated customer."))
            token_sudo = request.env['payment.token'].sudo().browse(token_id).exists()
            if (
                not token_sudo
                or not token_sudo.active
                or token_sudo.provider_id != provider_sudo
                or token_sudo.payment_method_id not in payment_methods_sudo
                or token_sudo.partner_id.commercial_partner_id
                != partner_sudo.commercial_partner_id
            ):
                raise AccessError(_("You do not have access to this payment token."))
        else:
            payment_method_sudo = payment_methods_sudo.filtered(
                lambda method: method.id == payment_method_id
            )
            if not payment_method_sudo or provider_sudo not in payment_method_sudo.provider_ids:
                raise ValidationError(_(
                    "The selected payment method is not available through this provider."
                ))
            token_id = None

        order_access_token = order_sudo._portal_ensure_token()
        kwargs.update({
            'provider_id': provider_sudo.id,
            'payment_method_id': payment_method_id,
            'token_id': token_id,
            'amount': order_sudo.amount_total,
            'currency_id': order_sudo.currency_id.id,
            'partner_id': partner_sudo.id,
            'tokenization_requested': bool(
                logged_in and kwargs.get('tokenization_requested')
            ),
            'landing_route': self._result_url(order_sudo, order_access_token),
            'sale_order_id': order_sudo.id,
        })
        kwargs.pop('csrf_token', None)
        kwargs.pop('is_validation', None)
        tx_sudo = self._create_transaction(
            custom_create_values={
                'sale_order_ids': [Command.set([order_sudo.id])],
                'logspace_order_id': order_sudo.id,
            },
            **kwargs,
        )
        return tx_sudo._get_processing_values()

    @http.route(
        '/logspace/booking/payment/result/<int:order_id>', type='http', methods=['GET'],
        auth='public', website=True, sitemap=False,
    )
    def logspace_payment_result(self, order_id, access_token=None, **_kwargs):
        """Display payment outcome without mutating the order or transaction."""
        try:
            order_sudo = self._check_logspace_order_access(order_id, access_token)
        except MissingError:
            return request.redirect('/logspace/booking/details')

        tx_sudo = order_sudo.sudo().transaction_ids.sorted('id', reverse=True)[:1]
        payment_state = tx_sudo.state if tx_sudo else 'not_found'
        if payment_state in ('done', 'cancel', 'error') or order_sudo.state == 'sale':
            request.session.pop('logspace_booking', None)
            request.session.pop('logspace_order_id', None)
            request.session.pop('logspace_tx_id', None)

        values = {
            'order': order_sudo,
            'tx': tx_sudo,
            'payment_state': payment_state,
            'order_number': order_sudo.name,
            'order_id': order_sudo.id,
            'order_confirmed': order_sudo.state == 'sale',
            'payment_accepted': order_sudo.payment_status == 'paid',
            'tracking_url': self._track_url(order_sudo, order_sudo._portal_ensure_token()),
            'retry_url': self._payment_url(order_sudo, order_sudo._portal_ensure_token()),
            'is_guest': request.env.user._is_public(),
            'guest_email': order_sudo.guest_email or '',
        }
        return self._secure_response(
            request.render(
                'appness_logspace.logspace_done_page', self._get_page_context(values),
            )
        )

    @http.route(
        '/logspace/booking/done', type='http', methods=['GET'], auth='public', website=True,
        sitemap=False,
    )
    def logspace_payment_result_legacy(self, order_id=None, access_token=None, **_kwargs):
        """Keep the old URL non-mutating while callers migrate to the protected result route."""
        order_id = self._cast_as_int(order_id)
        if not order_id or not access_token:
            return request.redirect('/logspace/booking/details')
        order_sudo = request.env['sale.order'].sudo().browse(order_id).exists()
        if not order_sudo or not order_sudo.is_logspace_order:
            return request.redirect('/logspace/booking/details')
        return request.redirect(self._result_url(order_sudo, access_token))
