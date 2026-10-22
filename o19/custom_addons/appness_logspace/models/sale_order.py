# -*- coding: utf-8 -*-

from datetime import timedelta
import hmac
import logging
import secrets

from odoo import _, api, fields, models, Command
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """Extend sale.order for Logspace logistics bookings"""
    _inherit = 'sale.order'

    # =========================================================================
    # Master Flag
    # =========================================================================
    is_logspace_order = fields.Boolean(
        string='Logspace Order',
        default=False,
        help='Check if this is a Logspace logistics order',
        index=True
    )

    # =========================================================================
    # Provider & Vehicle (visible if is_logspace_order)
    # =========================================================================
    logspace_provider_id = fields.Many2one(
        'res.partner',
        string='Logspace Provider',
        domain=[('is_provider', '=', True), ('state', '=', 'approved')],
        help='Assigned logistics service provider',
        index=True
    )
    logspace_vehicle_id = fields.Many2one(
        'logspace.vehicle',
        string='Assigned Vehicle',
        domain="[('provider_id', '=', logspace_provider_id), ('is_active', '=', True)]",
        help='Specific vehicle assigned to this booking'
    )
    logspace_driver_id = fields.Many2one(
        'res.partner',
        string='Driver',
        help='Assigned driver contact',
        # Mirrors logspace.vehicle.driver_id scoping, and restricted to contacts
        # actually flagged as drivers so only they get a driver portal account.
        domain="[('is_driver', '=', True), ('parent_id', '=', logspace_provider_id)]"
    )
    driver_phone = fields.Char(
        string='Driver Phone',
        related='logspace_driver_id.phone',
        readonly=False,
        help='Contact number for the assigned driver'
    )

    # =========================================================================
    # Route Information
    # =========================================================================
    pickup_zone_id = fields.Many2one(
        'logspace.zone',
        string='Pickup Zone',
        help='Zone where pickup will occur'
    )
    dropoff_zone_id = fields.Many2one(
        'logspace.zone',
        string='Dropoff Zone',
        help='Zone where dropoff will occur'
    )
    pickup_address = fields.Text(
        string='Pickup Address',
        required=False,
        help='Full pickup address with landmarks'
    )
    dropoff_address = fields.Text(
        string='Dropoff Address',
        required=False,
        help='Full dropoff address with landmarks'
    )

    # =========================================================================
    # Contact Information
    # =========================================================================
    pickup_contact_name = fields.Char(
        string='Pickup Contact Name',
        help='Person to contact at pickup location'
    )
    pickup_contact_phone = fields.Char(
        string='Pickup Contact Phone',
        help='Phone number for pickup contact'
    )
    dropoff_contact_name = fields.Char(
        string='Dropoff Contact Name',
        help='Person to contact at dropoff location'
    )
    dropoff_contact_phone = fields.Char(
        string='Dropoff Contact Phone',
        help='Phone number for dropoff contact'
    )

    # =========================================================================
    # Scheduling
    # =========================================================================
    scheduled_date = fields.Date(
        string='Scheduled Date',
        help='Date of the scheduled service'
    )
    pickup_timeframe = fields.Char(
        string='Pickup Time Frame',
        help='Time window for pickup (e.g., "10:00 - 12:00")'
    )
    dropoff_timeframe = fields.Char(
        string='Dropoff Time Frame',
        help='Time window for dropoff (e.g., "14:00 - 16:00")'
    )
    delivery_date = fields.Datetime(
        string='Actual Delivery Date',
        help='When the delivery was actually completed'
    )

    # =========================================================================
    # Item Details
    # =========================================================================
    item_description = fields.Text(
        string='Item Description',
        help='Description of items being transported'
    )
    special_instructions = fields.Text(
        string='Customer Special Instructions',
        help='Any special handling requirements from customer'
    )

    # =========================================================================
    # Add-ons
    # =========================================================================
    logspace_addon_ids = fields.Many2many(
        'logspace.addon',
        string='Add-ons',
        help='Selected add-on services'
    )

    # =========================================================================
    # Verification Codes (4-digit codes for pickup/dropoff verification)
    # =========================================================================
    verification_code_pickup = fields.Char(
        string='Pickup Verification Code',
        size=4,
        help='4-digit code shown to customer, driver confirms at pickup',
        readonly=True
    )
    verification_code_dropoff = fields.Char(
        string='Dropoff Verification Code',
        size=4,
        help='4-digit code shown to driver, customer confirms at dropoff',
        readonly=True
    )
    # Failed-entry counters. The codes are a 4-digit keyspace (9000 values); once
    # entry is exposed over HTTP through the driver portal an unthrottled compare
    # is brute-forceable, so attempts are capped and reset when a code is minted.
    verification_attempts_pickup = fields.Integer(
        string='Pickup Code Failed Attempts',
        default=0,
        readonly=True,
        copy=False,
    )
    verification_attempts_dropoff = fields.Integer(
        string='Dropoff Code Failed Attempts',
        default=0,
        readonly=True,
        copy=False,
    )

    # =========================================================================
    # Logistics State Workflow
    # =========================================================================
    logspace_state = fields.Selection([
        ('order_received', 'Order Received'),
        ('pickup_started', 'Pickup Started'),
        ('vendor_arrived_pickup', 'Vendor Arrived at Pickup'),
        ('pickup_addons', 'Pickup Add-ons Performed'),
        ('pickup_completed', 'Pickup Completed'),
        ('pre_dropoff_addons', 'Pre-Drop-off Add-ons'),
        ('arrived_destination', 'Arrived at Destination'),
        ('dropoff_completed', 'Drop-off Completed'),
        ('grace_period', 'Grace Period'),
        ('order_completed', 'Order Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Logspace Status',
       default=False,
       tracking=True,
       index=True,
       help='Current status of a confirmed logistics order',
    )
    logspace_state_label = fields.Char(
        string='Logspace Status Label',
        compute='_compute_logspace_state_label',
        help='Human-readable status, used by the status-change email templates.',
    )

    logspace_confirmation_processed = fields.Boolean(
        string='Logspace Confirmation Finalized',
        default=False,
        copy=False,
        readonly=True,
        help='Technical idempotency flag set after the standard sale confirmation is finalized.',
    )

    # =========================================================================
    # Guest Order Handling
    # =========================================================================
    is_guest_order = fields.Boolean(
        string='Guest Order',
        default=False,
        help='Order placed without user account (guest checkout)',
        index=True
    )
    guest_email = fields.Char(
        string='Guest Email',
        help='Email provided during guest checkout'
    )
    guest_phone = fields.Char(
        string='Guest Phone',
        help='Phone provided during guest checkout'
    )

    # =========================================================================
    # Payment summary (derived from standard Odoo payment transactions)
    # =========================================================================
    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ], string='Payment Status', default='pending')
    payment_method = fields.Selection([
        ('cod', 'Cash on Delivery'),
        ('paymob', 'Paymob'),
        ('other', 'Other'),
    ], string='Logspace Payment Method', default=False)
    transaction_ref = fields.Char(
        string='Transaction Reference',
        help='Payment gateway transaction reference'
    )

    def _get_blocking_logspace_transactions(self, draft_retry_after=None):
        """Return transactions that make a new or changed payment attempt unsafe."""
        self.ensure_one()
        retry_after = draft_retry_after or timedelta(minutes=30)
        retry_cutoff = fields.Datetime.now() - retry_after
        return self.transaction_ids.sudo().filtered(
            lambda transaction: (
                transaction.state in ('pending', 'authorized', 'done')
                or (
                    transaction.state == 'draft'
                    and transaction.create_date >= retry_cutoff
                )
            )
        )

    def _sync_logspace_payment_fields(self):
        """Derive the legacy summary fields from canonical Odoo transactions."""
        for order in self.sudo().filtered('is_logspace_order'):
            transactions = order.transaction_ids.filtered(
                lambda transaction: (
                    transaction.operation != 'validation'
                    and transaction.currency_id == order.currency_id
                    and order.currency_id.compare_amounts(transaction.amount, 0) > 0
                )
            )
            successful = transactions.filtered(
                lambda transaction: transaction.state in ('authorized', 'done')
            ).sorted('id', reverse=True)
            pending = transactions.filtered(
                lambda transaction: transaction.state in ('draft', 'pending')
            ).sorted('id', reverse=True)
            failed = transactions.filtered(
                lambda transaction: transaction.state in ('cancel', 'error')
            ).sorted('id', reverse=True)

            fully_paid = successful and order.currency_id.compare_amounts(
                order.amount_paid, order.amount_total,
            ) >= 0
            if fully_paid:
                status = 'paid'
                transaction = successful[0]
            elif successful or pending:
                status = 'pending'
                transaction = (successful or pending)[0]
            elif failed:
                status = 'failed'
                transaction = failed[0]
            else:
                status = 'pending'
                transaction = self.env['payment.transaction']

            values = {'payment_status': status}
            if transaction:
                values.update({
                    'payment_method': 'other',
                    'transaction_ref': transaction.provider_reference or transaction.reference,
                })
            else:
                values.update({
                    'payment_method': False,
                    'transaction_ref': False,
                })

            if status == 'paid':
                if not order.logspace_state:
                    values['logspace_state'] = 'order_received'
                if not order.logspace_confirmation_processed:
                    values['logspace_confirmation_processed'] = True
                if not order.verification_code_pickup:
                    values['verification_code_pickup'] = self._generate_verification_code()
                    values['verification_attempts_pickup'] = 0

            order.write(values)

            if status == 'paid':
                provider_name = (
                    transaction.provider_id.name
                    if transaction and transaction.provider_id
                    else _('Payment Gateway')
                )
                order._create_timeline_event(
                    'payment_received',
                    _(
                        'Payment accepted through %(provider)s (reference: %(reference)s)',
                        provider=provider_name,
                        reference=transaction.provider_reference or transaction.reference if transaction else '',
                    ),
                    unique=True,
                )
                if values.get('logspace_state') == 'order_received':
                    order._create_timeline_event(
                        'order_received',
                        _('Order received and confirmed'),
                        unique=True,
                    )
                # Core Odoo confirms the sale order from _post_process (and
                # emails the customer there), but only when the transaction
                # was linked through sale_order_ids up front. A paid order
                # must never remain a quotation - providers cannot act on it -
                # so confirm here on any other path (later link, migration
                # backfill). Deliberately without send_email: this matches a
                # manual backend confirmation, and keeps upgrade backfills
                # from emailing customers about old orders.
                if order.state in ('draft', 'sent'):
                    order.action_confirm()

    # =========================================================================
    # Customer Rating (simple rating on order)
    # =========================================================================
    logspace_customer_rating = fields.Integer(
        string='Customer Rating',
        help='Customer rating from 1 to 5 stars'
    )
    logspace_customer_rating_comment = fields.Text(
        string='Customer Review Comment',
        help='Optional comment from the customer'
    )

    # =========================================================================
    # Related Records
    # =========================================================================
    timeline_ids = fields.One2many(
        'logspace.order.timeline',
        'order_id',
        string='Tracking Timeline',
        readonly=True
    )

    # =========================================================================
    # Smart Button Counts
    # =========================================================================
    logspace_ticket_ids = fields.One2many(
        'helpdesk.ticket',
        'logspace_order_id',
        string='Tickets'
    )
    logspace_ticket_count = fields.Integer(
        string='# Tickets',
        compute='_compute_logspace_counts'
    )

    logspace_refund_ids = fields.One2many(
        'logspace.refund',
        'order_id',
        string='Refund Requests'
    )
    logspace_refund_count = fields.Integer(
        string='Refunds',
        compute='_compute_logspace_counts'
    )

    logspace_provider_bill_id = fields.Many2one(
        'account.move',
        string='Provider Bill',
        copy=False,
        readonly=True,
        help='Vendor bill created for the provider upon order completion'
    )
    logspace_provider_bill_count = fields.Integer(
        string='Provider Bills',
        compute='_compute_logspace_counts'
    )

    # What the price matrix QUOTED for the booked route, snapshotted at
    # booking time. The bill pays the quoted provider price so the platform
    # never charges its own fee on the fee: the matrix says customer =
    # provider + fee, so taking commission as a percentage of the customer
    # subtotal would bill 10% of (provider + fee) and underpay the provider.
    # Orders created outside the portal (no matrix) leave these empty and the
    # bill falls back to the legacy percentage-of-subtotal formula.
    logspace_quoted_provider_price = fields.Monetary(
        string='Quoted Provider Price',
        currency_field='currency_id',
        copy=False,
        readonly=True,
        help="Provider's price as quoted by the price matrix at booking time"
    )
    logspace_quoted_platform_fee = fields.Monetary(
        string='Quoted Platform Fee',
        currency_field='currency_id',
        copy=False,
        readonly=True,
        help='Platform fee as quoted by the price matrix at booking time'
    )

    # What the provider is actually paid, mirrored from the commission bill.
    #
    # Stored + computed rather than `related`: group_logspace_provider implies
    # only base.group_user, and core grants account.move read to the account
    # groups or to portal users - not to internal users. fields._compute_related
    # traverses with the CURRENT env and re-raises AccessError (it does not
    # sudo), so a related field would break the Logspace order list for every
    # provider. Storing it also means the list stays sortable and the amount is
    # read straight from the column.
    #
    # sudo() inside the compute is what lets a provider read his own payout
    # without an account.move ACL on the ORDER; the Provider Bills menu is where
    # the ACL actually applies.
    logspace_provider_bill_amount = fields.Monetary(
        string='Provider Payout',
        currency_field='currency_id',
        compute='_compute_logspace_provider_bill_amount',
        store=True,
        help='Untaxed total of the provider commission bill - what the provider is paid'
    )
    logspace_provider_commission_rate = fields.Float(
        string='Commission',
        compute='_compute_logspace_provider_bill_amount',
        store=True,
        help='Platform commission applied to this order, as a fraction of the order total'
    )

    @api.depends('logspace_provider_bill_id.amount_untaxed', 'amount_total')
    def _compute_logspace_provider_bill_amount(self):
        for order in self:
            # sudo: a provider has no account.move read access on the order's
            # bill outside the Provider Bills menu's own ACL + record rule.
            bill = order.sudo().logspace_provider_bill_id
            # amount_untaxed, not amount_total: the bill line is created for the
            # exact payout, but any purchase tax on the bill inflates
            # amount_total above what the provider is actually paid.
            order.logspace_provider_bill_amount = bill.amount_untaxed if bill else 0.0
            if bill and order.amount_total:
                order.logspace_provider_commission_rate = (
                    order.amount_total - bill.amount_untaxed
                ) / order.amount_total
            else:
                order.logspace_provider_commission_rate = 0.0

    @api.depends('logspace_ticket_ids', 'logspace_refund_ids', 'logspace_provider_bill_id')
    def _compute_logspace_counts(self):
        """Compute counts for smart buttons"""
        for order in self:
            order.logspace_ticket_count = len(order.logspace_ticket_ids)
            order.logspace_refund_count = len(order.logspace_refund_ids)
            order.logspace_provider_bill_count = 1 if order.logspace_provider_bill_id else 0

    def action_view_logspace_tickets(self):
        """Open tickets for this order"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "helpdesk.ticket",
            "view_mode": "list,form",
            "domain": [('logspace_order_id', '=', self.id)],
            "context": {'default_logspace_order_id': self.id}
        }

    def action_view_logspace_refunds(self):
        """Open refunds for this order"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "logspace.refund",
            "view_mode": "list,form",
            "domain": [('order_id', '=', self.id)],
            "context": {'default_order_id': self.id}
        }

    def action_view_logspace_provider_bill(self):
        """Open the vendor bill created for the provider"""
        self.ensure_one()
        if not self.logspace_provider_bill_id:
            return
        return {
            'name': _('Provider Bill'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            # Pin the module's own read-only form: core's bill form renders
            # journal_id, which base.group_user cannot read, so a provider
            # opening this smart button would hit an AccessError.
            'views': [(self.env.ref(
                'appness_logspace.view_logspace_provider_bill_form').id, 'form')],
            'res_id': self.logspace_provider_bill_id.id,
            'context': {'default_move_type': 'in_invoice'},
        }

    # =========================================================================
    # Actions - Workflow (Updated to match logspace_state field states)
    # =========================================================================

    @staticmethod
    def _generate_verification_code():
        """Return a cryptographically secure four-digit verification code."""
        return str(secrets.randbelow(9000) + 1000)

    def _create_timeline_event(self, event_type, description, *, unique=False):
        """Create a timeline event, optionally only once per order and event type."""
        for order in self:
            if unique and self.env['logspace.order.timeline'].sudo().search_count([
                ('order_id', '=', order.id),
                ('event_type', '=', event_type),
            ], limit=1):
                continue
            self.env['logspace.order.timeline'].sudo().create({
                'order_id': order.id,
                'event_type': event_type,
                'description': description,
                'event_time': fields.Datetime.now(),
            })

    def _notify_driver_assigned(self):
        """Email the assigned driver and the customer about an assignment.

        Called from write() when logspace_driver_id changes and from
        _finalize_logspace_confirmation() for the driver derived from the
        vehicle at booking time. Skips unconfirmed orders so the confirmation
        hook is the one that notifies (and therefore only ever notifies once).
        """
        self.ensure_one()
        # Upgrade backfills confirm historical orders with this flag set; an
        # assignment email about a weeks-old order is noise (see the 19.0.2.4.0
        # migration, whose docstring promises a silent confirm).
        if self.env.context.get('logspace_skip_status_emails'):
            return False
        driver = self.logspace_driver_id
        if not driver or self.state != 'sale':
            return False

        notified = []
        if driver.email:
            template = self.env.ref(
                'appness_logspace.email_template_driver_assignment_notice',
                raise_if_not_found=False,
            )
            if template:
                try:
                    template.sudo().send_mail(self.id, force_send=True)
                except Exception as error:  # never block the order on a mail failure
                    _logger.warning(
                        "Driver assignment email failed for %s: %s", self.name, error,
                    )
                else:
                    notified.append('the driver (%s)' % driver.name)
        if self.partner_id:
            template = self.env.ref(
                'appness_logspace.email_template_driver_assigned',
                raise_if_not_found=False,
            )
            if template:
                # Tokenize before rendering: the customer track link only opens
                # for a guest when it carries the order's access token.
                self.sudo()._portal_ensure_token()
                try:
                    template.sudo().send_mail(self.id, force_send=True)
                except Exception as error:  # never block the order on a mail failure
                    _logger.warning(
                        "Driver-assigned customer email failed for %s: %s",
                        self.name, error,
                    )
                else:
                    notified.append('the customer (%s)' % self.partner_id.name)
        if notified:
            self.sudo().message_post(body=_(
                'Delivery assignment emailed to %(recipients)s.',
                recipients=' and '.join(notified),
            ))
        return bool(notified)

    @api.depends('logspace_state')
    def _compute_logspace_state_label(self):
        selection_labels = dict(self._fields['logspace_state'].selection)
        for order in self:
            order.logspace_state_label = selection_labels.get(
                order.logspace_state, order.logspace_state or '',
            )

    def _notify_logspace_status_change(self, previous_state):
        """Email the customer, the provider and the driver about a status change.

        Called from write() whenever `logspace_state` actually changes. Each
        party gets its OWN email (one template, one recipient), so nobody sees
        the other parties' addresses. Only the customer's template renders the
        verification codes - the driver must obtain the codes from the
        customer, so they never reach him by email.
        """
        self.ensure_one()
        if self.env.context.get('logspace_skip_status_emails'):
            return
        if not self.is_logspace_order or self.state != 'sale':
            return
        if self.logspace_state == previous_state:
            return

        # The "order delivered" email is already sent to the customer on
        # completion - don't bury it under a second email for the same event.
        recipients = [
            ('email_template_logspace_status_customer', bool(self.partner_id)),
            ('email_template_logspace_status_provider', bool(self.logspace_provider_id)),
            ('email_template_logspace_status_driver', bool(self.logspace_driver_id)),
        ]
        if self.logspace_state == 'order_completed':
            recipients[0] = ('email_template_logspace_status_customer', False)

        for template_xmlid, wanted in recipients:
            template = self.env.ref(
                'appness_logspace.%s' % template_xmlid, raise_if_not_found=False,
            )
            if not wanted or not template:
                continue
            if template_xmlid == 'email_template_logspace_status_customer':
                # The customer template's track link carries the access token,
                # so a guest can open it; generate the token before rendering.
                self.sudo()._portal_ensure_token()
            try:
                template.sudo().send_mail(self.id, force_send=True)
            except Exception as error:  # never block the order on a mail failure
                _logger.warning(
                    "Logspace status email %s failed for %s: %s",
                    template_xmlid, self.name, error,
                )

    def _finalize_logspace_confirmation(self):
        """Apply Logspace-only side effects after Odoo confirms the sale order."""
        for order in self.filtered(
            lambda candidate: (
                candidate.is_logspace_order
                and candidate.state == 'sale'
                and not candidate.logspace_confirmation_processed
            )
        ):
            values = {
                'logspace_confirmation_processed': True,
                'logspace_state': order.logspace_state or 'order_received',
            }
            if not order.verification_code_pickup:
                values['verification_code_pickup'] = self._generate_verification_code()
                values['verification_attempts_pickup'] = 0
            order.write(values)
            order._create_timeline_event(
                'order_received', 'Order received and confirmed', unique=True,
            )
            # The driver is usually derived from the vehicle at booking time, so
            # write() never sees logspace_driver_id change - notify from here.
            if order.logspace_driver_id:
                order._notify_driver_assigned()

            for user in order.partner_id.sudo().user_ids.filtered(
                lambda candidate: candidate.active
            ):
                self.env['logspace.notification'].sudo().create_notification(
                    user_id=user.id,
                    title=_('Booking Confirmed'),
                    message=_('Your booking %s has been confirmed.', order.name),
                    type='success',
                    action_link=f'/my/orders/{order.id}',
                )

    def action_confirm(self):
        """Let Odoo confirm the order, then finalize Logspace exactly once."""
        logspace_orders = self.filtered(
            lambda order: order.is_logspace_order and order.state in ('draft', 'sent')
        )
        result = super().action_confirm()
        logspace_orders._finalize_logspace_confirmation()
        return result

    def _check_logspace_refund_not_approved(self):
        """Check if an approved refund exists for this order and raise error if so"""
        self.ensure_one()
        approved_refund = self.env['logspace.refund'].sudo().search([
            ('order_id', '=', self.id),
            ('state', 'in', ['approved', 'processed']),
        ], limit=1)
        if approved_refund:
            raise UserError(_(
                'Cannot proceed: an approved refund (%(refund)s) exists for this order.\n'
                'The delivery process is blocked until the refund is resolved.'
            ) % {'refund': approved_refund.name})

    def _is_logspace_provider_user(self):
        """True when the current user is a provider-group user without admin rights."""
        return (
            not self.env.su
            and not self.env.user._is_superuser()
            and not self.env.user.has_group('base.group_system')
            and self.env.user.has_group('appness_logspace.group_logspace_provider')
        )

    # Maximum wrong code entries before the order locks. The codes are a 4-digit
    # keyspace, so an unthrottled HTTP endpoint is brute-forceable.
    MAX_VERIFICATION_ATTEMPTS = 5

    # Delivery steps a driver may advance from the portal, in workflow order.
    #   method        - called when no customer code is required
    # apply_method    - called once the code has been verified (skips the backend
    #                   wizard, which a portal user has no ACL for)
    #   code_type     - 'pickup' / 'dropoff' when the customer's code is required
    #   from_states   - the single state each step is offered from. Deliberately
    #                   STRICTER than the target method's own `expected_states`,
    #                   and matching the `invisible=` conditions on the backend
    #                   buttons instead: a driver must see exactly one button and
    #                   advance one step at a time, so two steps that the model
    #                   would both accept from the same state are never offered
    #                   together. Every entry below therefore names one state, and
    #                   the chain is strictly linear.
    #
    # The model's wider `expected_states` are left as they are on purpose. They
    # are what lets an admin or a provider rescue an order that has skipped or
    # stalled on an intermediate step, and narrowing them would remove that.
    # Only the driver-facing list - and action_driver_transition, which enforces
    # it - are strict.
    _LOGSPACE_DRIVER_ACTIONS = {
        'start_pickup': {
            'label': 'Start Pickup',
            'method': 'action_start_pickup',
            'code_type': False,
            'from_states': ('order_received',),
        },
        'vendor_arrived_pickup': {
            'label': 'Arrived at Pickup',
            'method': 'action_vendor_arrived_pickup',
            'code_type': False,
            'from_states': ('pickup_started',),
        },
        'pickup_addons': {
            'label': 'Pickup Add-ons Done',
            'method': 'action_pickup_addons',
            'code_type': False,
            'from_states': ('vendor_arrived_pickup',),
        },
        'pickup_completed': {
            'label': 'Pickup Completed',
            'apply_method': '_apply_pickup_completed',
            'code_type': 'pickup',
            'from_states': ('pickup_addons',),
            'highlight': True,
        },
        'pre_dropoff_addons': {
            'label': 'Pre-Dropoff Add-ons',
            'method': 'action_pre_dropoff_addons',
            'code_type': False,
            'from_states': ('pickup_completed',),
        },
        'arrived_destination': {
            'label': 'Arrived at Destination',
            'method': 'action_arrived_destination',
            'code_type': False,
            'from_states': ('pre_dropoff_addons',),
        },
        'dropoff_completed': {
            'label': 'Dropoff Completed',
            'apply_method': '_apply_dropoff_completed',
            'code_type': 'dropoff',
            'from_states': ('arrived_destination',),
            'highlight': True,
        },
    }

    def _is_logspace_driver_user(self):
        """True when the current user is a driver portal user.

        Unlike _is_logspace_provider_user this deliberately ignores `env.su`:
        the driver portal controller loads orders with sudo(), and the
        authorization must still hold against the real session user.
        """
        user = self.env.user
        return (
            not user._is_superuser()
            and user.has_group('appness_logspace.group_logspace_driver')
            and bool(user.partner_id.is_driver)
        )

    def _check_logspace_driver_access(self):
        """Raise unless the session user is the driver assigned to this order."""
        self.ensure_one()
        if not self._is_logspace_driver_user():
            raise AccessError(_('Only the assigned driver can update this delivery.'))
        if self.logspace_driver_id != self.env.user.partner_id:
            raise AccessError(_('Only the assigned driver can update this delivery.'))

    def _verify_logspace_code(self, code_type, entered_code):
        """Validate a customer verification code. Returns True when correct.

        Single source of truth shared by the backend wizard and the driver
        portal, so the two cannot drift apart.
        """
        self.ensure_one()
        if code_type not in ('pickup', 'dropoff'):
            raise UserError(_('Unknown verification code type.'))

        attempts_field = 'verification_attempts_%s' % code_type
        code_field = 'verification_code_%s' % code_type
        label = _('pickup') if code_type == 'pickup' else _('drop-off')
        order_sudo = self.sudo()

        # The throttle protects the driver's HTTP endpoint from brute force.
        # Providers are internal users working the backend wizard, so letting a
        # driver exhaust the counter must not lock the provider out of rescuing
        # the delivery - otherwise "contact your provider" is a dead end.
        #
        # _is_logspace_provider_user() is the discriminator, and it must not be
        # replaced by a bare `env.su` test: the driver portal controller loads
        # orders with .sudo() (controllers/driver.py:76), so env.su is True for
        # every driver request and such a check would let a locked-out driver
        # straight through. _is_logspace_provider_user() already returns False
        # under sudo(), which keeps the cap enforced on the portal path.
        enforce_cap = not self._is_logspace_provider_user()

        if enforce_cap and order_sudo[attempts_field] >= self.MAX_VERIFICATION_ATTEMPTS:
            raise UserError(_(
                'Too many incorrect %(label)s codes for order %(order)s. '
                'Contact your provider to continue this delivery.',
                label=label, order=self.name,
            ))

        expected = order_sudo[code_field] or ''
        entered = (entered_code or '').strip()

        # Reject blanks outright. Comparing '' against an unset code would
        # otherwise succeed and skip verification entirely.
        if not entered:
            raise UserError(_('Enter the %(label)s verification code.', label=label))
        if not expected:
            raise UserError(_(
                'No %(label)s verification code has been generated for order %(order)s yet.',
                label=label, order=self.name,
            ))

        if not hmac.compare_digest(entered, expected):
            attempts = order_sudo[attempts_field] + 1
            order_sudo.write({attempts_field: attempts})
            remaining = self.MAX_VERIFICATION_ATTEMPTS - attempts
            if enforce_cap and remaining <= 0:
                raise UserError(_(
                    'Incorrect %(label)s code. This order is now locked - '
                    'contact your provider to continue the delivery.',
                    label=label,
                ))
            if remaining <= 0:
                # A provider is never locked out, so do not tell them they are.
                raise UserError(_('Incorrect %(label)s code.', label=label))
            raise UserError(_(
                'Incorrect %(label)s code. Ask the customer and try again '
                '(%(remaining)s attempts left).',
                label=label, remaining=remaining,
            ))

        order_sudo.write({attempts_field: 0})
        return True

    def _get_logspace_driver_actions(self):
        """Delivery actions for the driver portal, with availability for the
        current state. Never exposes the expected codes."""
        self.ensure_one()
        actions = []
        for key, spec in self._LOGSPACE_DRIVER_ACTIONS.items():
            actions.append({
                'key': key,
                'label': _(spec['label']),
                'needs_code': bool(spec['code_type']),
                'code_type': spec['code_type'] or '',
                'highlight': bool(spec.get('highlight')),
                'available': self.state == 'sale' and self.logspace_state in spec['from_states'],
            })
        return actions

    def action_driver_transition(self, action_key, code=None):
        """Apply a driver-portal status transition.

        Delegates to the existing transition methods so there is exactly one
        implementation of the workflow. Code-requiring steps call the `_apply_*`
        variant directly, because the backend verification wizard is a
        TransientModel the driver portal user has no ACL for.
        """
        self.ensure_one()
        if not self.is_logspace_order:
            raise UserError(_('This is not a Logspace order.'))

        spec = self._LOGSPACE_DRIVER_ACTIONS.get(action_key)
        if not spec:
            raise UserError(_('Unknown delivery action.'))

        self._check_logspace_driver_access()

        # Enforce the one-step-at-a-time rule here, not only in the rendered
        # button list. Hiding a button is cosmetic: this method is reachable from
        # /logspace/driver/orders/action with a hand-built request, and the target
        # methods accept a WIDER set of states than the driver spec does (on
        # purpose, so admins and providers can rescue an order that skipped a
        # step). Without this check nothing would stop a driver jumping ahead.
        # Reading spec['from_states'] is what keeps the renderer and the enforcer
        # honest against each other - there is one list, not two.
        self._require_logspace_transition(spec['from_states'], _(spec['label']))

        if spec['code_type']:
            self._verify_logspace_code(spec['code_type'], code)
            method_name = spec['apply_method']
        else:
            method_name = spec['method']

        getattr(self, method_name)()
        return True

    def _get_verification_wizard_action(self, code_type):
        """Open the customer verification wizard for provider users.
        Returns False for admins/system users (they bypass verification)."""
        if not self._is_logspace_provider_user():
            return False
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customer Verification Required'),
            'res_model': 'logspace.verification.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('appness_logspace.logspace_verification_wizard_view_form').id,
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_code_type': code_type,
            },
        }

    def action_logspace_confirm(self):
        """Compatibility helper for already-confirmed orders."""
        self._finalize_logspace_confirmation()

    def _require_logspace_transition(self, expected_states, action_label):
        """Raise a loud error when the order may not transition.

        Status buttons used to silently no-op when the sale order was not
        confirmed (state != 'sale') or the logspace status did not match,
        which made them look broken to providers.
        """
        self.ensure_one()
        if self.state != 'sale':
            raise UserError(_(
                'Cannot %(action)s: order %(order)s is not confirmed yet '
                '(payment pending). Confirm the order first.',
                action=action_label,
                order=self.name,
            ))
        if self.logspace_state not in expected_states:
            current_label = dict(self._fields['logspace_state'].selection).get(
                self.logspace_state, self.logspace_state or _('None'),
            )
            expected_labels = ', '.join(
                dict(self._fields['logspace_state'].selection).get(s, s)
                for s in expected_states
            )
            raise UserError(_(
                'Cannot %(action)s: order %(order)s is in status "%(current)s". '
                'Expected status: %(expected)s.',
                action=action_label,
                order=self.name,
                current=current_label,
                expected=expected_labels,
            ))

    def action_start_pickup(self):
        """Driver starts pickup - triggered when driver begins journey to pickup"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            order._require_logspace_transition(['order_received'], _('start pickup'))
            order._check_logspace_refund_not_approved()
            # sudo: providers may only change status through the action buttons
            order.sudo().logspace_state = 'pickup_started'
            order._create_timeline_event('pickup_started', _('Pickup journey started'))

    def action_vendor_arrived_pickup(self):
        """Vendor/driver arrived at pickup location"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            order._require_logspace_transition(['pickup_started'], _('mark vendor arrived at pickup'))
            order._check_logspace_refund_not_approved()
            order.sudo().logspace_state = 'vendor_arrived_pickup'
            order._create_timeline_event('vendor_arrived_pickup', _('Vendor arrived at pickup location'))

    def action_pickup_addons(self):
        """Pickup add-ons performed (loading assistance, etc.)"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            order._require_logspace_transition(['vendor_arrived_pickup'], _('perform pickup add-ons'))
            order._check_logspace_refund_not_approved()
            order.sudo().logspace_state = 'pickup_addons'
            order._create_timeline_event('pickup_addons', 'Pickup add-ons performed')

    def action_pickup_completed(self):
        """Pickup completed - items loaded, driver departs.
        Providers must first verify the customer's pickup code (wizard).
        Admins bypass the verification."""
        wizard_action = self._get_verification_wizard_action('pickup')
        if wizard_action:
            return wizard_action
        return self._apply_pickup_completed()

    def _apply_pickup_completed(self):
        """Apply the pickup completion transition (code already verified)."""
        for order in self.filtered(lambda o: o.is_logspace_order):
            order._require_logspace_transition(
                ['pickup_started', 'vendor_arrived_pickup', 'pickup_addons'],
                _('complete pickup'),
            )
            order._check_logspace_refund_not_approved()
            order.sudo().logspace_state = 'pickup_completed'
            order._create_timeline_event('pickup_completed', 'Pickup completed, items loaded')
        return True

    def action_pre_dropoff_addons(self):
        """Pre-drop-off add-ons performed"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            order._require_logspace_transition(['pickup_completed'], _('perform pre-drop-off add-ons'))
            order._check_logspace_refund_not_approved()
            order.sudo().logspace_state = 'pre_dropoff_addons'
            order._create_timeline_event('pre_dropoff_addons', 'Pre-drop-off add-ons performed')

    def action_arrived_destination(self):
        """Driver arrived at destination/dropoff"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            order._require_logspace_transition(
                ['pickup_completed', 'pre_dropoff_addons'],
                _('mark arrived at destination'),
            )
            order._check_logspace_refund_not_approved()
            # Generate dropoff code if not set
            if not order.verification_code_dropoff:
                order.sudo().write({
                    'verification_code_dropoff': self._generate_verification_code(),
                    'verification_attempts_dropoff': 0,
                })
            order.sudo().logspace_state = 'arrived_destination'
            order._create_timeline_event('arrived_destination', _('Arrived at destination'))

    def action_dropoff_completed(self):
        """Drop-off completed - items delivered.
        Providers must first verify the customer's drop-off code (wizard).
        Admins bypass the verification."""
        wizard_action = self._get_verification_wizard_action('dropoff')
        if wizard_action:
            return wizard_action
        return self._apply_dropoff_completed()

    def _apply_dropoff_completed(self):
        """Apply the drop-off completion transition (code already verified)."""
        for order in self.filtered(lambda o: o.is_logspace_order):
            order._require_logspace_transition(['arrived_destination'], _('complete drop-off'))
            order._check_logspace_refund_not_approved()
            order.sudo().write({
                'logspace_state': 'dropoff_completed',
                'delivery_date': fields.Datetime.now(),
            })
            order._create_timeline_event('dropoff_completed', 'Drop-off completed')
        return True

    def action_start_grace_period(self):
        """Start grace period after dropoff"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            order._require_logspace_transition(['dropoff_completed'], _('start grace period'))
            order._check_logspace_refund_not_approved()
            order.sudo().logspace_state = 'grace_period'
            order._create_timeline_event('grace_period', _('Grace period started'))

    def action_complete_order(self):
        """Final order completion"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            order._require_logspace_transition(
                ['dropoff_completed', 'grace_period'], _('complete order'),
            )
            order._check_logspace_refund_not_approved()
            order.sudo().logspace_state = 'order_completed'
            order._create_timeline_event('order_completed', _('Order fully completed'))

            # Send order completion email
            try:
                template = self.env.ref('appness_logspace.email_template_order_delivered')
                if template:
                    template.send_mail(order.id, force_send=True)
            except Exception:
                pass

            # Create provider vendor bill
            order._create_provider_bill()

    def action_admin_complete_order(self):
        """Admin testing action: force complete the order and create the provider bill."""
        for order in self.filtered(lambda o: o.is_logspace_order):
            order._require_logspace_transition(
                [s for s, _label in self._fields['logspace_state'].selection if s != 'order_completed'],
                _('force complete order'),
            )
            order._check_logspace_refund_not_approved()
            order.sudo().logspace_state = 'order_completed'
            order._create_timeline_event('order_completed', _('Order completed by administrator'), unique=True)

            try:
                template = self.env.ref('appness_logspace.email_template_order_delivered', raise_if_not_found=False)
                if template:
                    template.send_mail(order.id, force_send=True)
            except Exception:
                pass

            order._create_provider_bill()

    def _create_provider_bill(self):
        """Create a vendor bill for the provider upon order completion with platform fee deducted."""
        AccountMove = self.env['account.move'].sudo()
        for order in self.filtered('is_logspace_order'):
            if order.logspace_provider_bill_id:
                _logger.info('Provider bill already exists for order %s (bill ID %s)', order.name, order.logspace_provider_bill_id.id)
                continue
            if not order.logspace_provider_id:
                _logger.warning('Cannot create provider bill for order %s: no provider assigned', order.name)
                continue

            provider = order.logspace_provider_id
            fee_pct = provider.platform_fee_percentage or 0.0
            multiplier = fee_pct / 100.0 if fee_pct > 1.0 else fee_pct
            # Commission is computed on the UNTAXED product subtotal (truck
            # service + add-ons are all provider-delivered, so both are
            # commissionable): tax must not inflate the fee. The provider is
            # still paid out of what the customer actually paid (amount_total,
            # and customer payments are always 100% of it) - the platform
            # keeps the tax difference.
            untaxed_subtotal = sum(order.order_line.mapped('price_subtotal'))

            service_tmpl = self.env.ref(
                'appness_logspace.product_logspace_service_product_template',
                raise_if_not_found=False
            )
            service_product = service_tmpl.product_variant_id if service_tmpl else False

            # A portal booking carries the price matrix's quote: the customer
            # price is provider + fee, so commission as a percentage of the
            # subtotal would charge the platform's own fee on the fee (90
            # quoted at 10% -> customer 99 -> 9.9 commission instead of 9).
            # Honor the quote: the quoted fee is taken flat, add-ons stay
            # commissionable at the provider's rate.
            if order.logspace_quoted_provider_price or order.logspace_quoted_platform_fee:
                service_untaxed = sum(
                    line.price_subtotal for line in order.order_line
                    if line.product_id and service_product
                    and line.product_id.product_tmpl_id == service_product.product_tmpl_id
                )
                addon_untaxed = untaxed_subtotal - service_untaxed
                commission_amount = order.currency_id.round(
                    order.logspace_quoted_platform_fee + addon_untaxed * multiplier
                )
            else:
                commission_amount = order.currency_id.round(untaxed_subtotal * multiplier)
            provider_amount = order.amount_total - commission_amount

            if provider_amount <= 0:
                _logger.warning(
                    'Provider bill skipped for order %s: provider %s (id %s) would be'
                    ' paid %.2f with a %.1f%% platform fee - check the fee'
                    ' configuration or the order amounts.',
                    order.name, provider.name, provider.id, provider_amount,
                    multiplier * 100,
                )
                continue

            if order.logspace_quoted_provider_price or order.logspace_quoted_platform_fee:
                fee_desc = _(
                    '%(fee)s quoted + %(pct)s of add-ons',
                    fee=order.currency_id.format(order.logspace_quoted_platform_fee or 0.0),
                    pct=f'{multiplier * 100:.1f}%',
                )
            else:
                fee_desc = _('%(pct)s of the order', pct=f'{multiplier * 100:.1f}%')

            line_vals = {
                'name': _(
                    'Logistics Services - %(order)s (Order Total: %(total)s, Platform Fee: %(fee)s)',
                    order=order.name,
                    total=order.currency_id.format(order.amount_total),
                    fee=fee_desc,
                ),
                'quantity': 1.0,
                'price_unit': provider_amount,
            }
            if service_product:
                line_vals['product_id'] = service_product.id

            bill_vals = {
                'move_type': 'in_invoice',
                'partner_id': provider.id,
                'company_id': order.company_id.id,
                'currency_id': order.currency_id.id,
                'invoice_date': fields.Date.context_today(order),
                'ref': _('Logistics payout for %s', order.name),
                'invoice_origin': order.name,
                'is_logspace_provider_bill': True,
                'invoice_line_ids': [Command.create(line_vals)],
            }

            try:
                bill = AccountMove.create(bill_vals)
                order.logspace_provider_bill_id = bill.id
                # Post immediately: bills that stayed draft forever were
                # indistinguishable from "no bill" on the provider's bill list.
                # Known failure modes (no purchase journal, tax config) are
                # caught below - the bill stays draft, still linked to the order.
                bill.action_post()
                order.message_post(
                    body=_(
                        'Provider vendor bill <a href="#" data-oe-model="account.move" data-oe-id="%(bill_id)s">%(bill_name)s</a> '
                        'created for %(provider)s (Amount: %(amount)s, Deducted Platform Fee: %(fee)s).',
                        bill_id=bill.id,
                        bill_name=bill.name or bill.ref or 'Draft Bill',
                        provider=provider.name,
                        amount=order.currency_id.format(provider_amount),
                        fee=fee_desc,
                    )
                )
            except (UserError, ValidationError, AccessError) as e:
                _logger.error('Failed to create/post provider bill for order %s: %s', order.name, str(e))

    def action_cancel_logspace(self):
        """Cancel logistics order"""
        # Logspace admins may cancel even with an approved/processed refund
        # request: the customer explicitly asked for the refund, so blocking
        # the cancellation leaves the order stuck.
        is_logspace_admin = (
            self.env.su
            or self.env.user.has_group('appness_logspace.group_logspace_admin')
        )
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state in ['order_completed', 'dropoff_completed']:
                raise UserError(_(
                    'Cannot cancel order %(order)s: it is already in status "%(status)s".',
                    order=order.name,
                    status=dict(order._fields['logspace_state'].selection).get(
                        order.logspace_state, order.logspace_state),
                ))
            if not is_logspace_admin:
                order._check_logspace_refund_not_approved()
            order.sudo().logspace_state = 'cancelled'
            order._create_timeline_event('cancelled', 'Order cancelled')

    def action_reset_logspace_to_draft(self):
        """Reset cancelled logistics order back to order_received"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state != 'cancelled':
                raise UserError(_(
                    'Cannot reset order %(order)s: only cancelled orders can be reset.',
                    order=order.name,
                ))
            order._check_logspace_refund_not_approved()
            order.sudo().logspace_state = 'order_received'
            order._create_timeline_event('order_received', _('Order reset to received from cancelled'))

    # =========================================================================
    # Override Create
    # =========================================================================
    @api.onchange('logspace_provider_id')
    def _onchange_logspace_provider_id(self):
        """Auto-set salesperson (user_id) when provider is assigned"""
        if self.logspace_provider_id and self.is_logspace_order:
            if self.logspace_provider_id.user_ids:
                self.user_id = self.logspace_provider_id.user_ids[0]
            else:
                self.user_id = False

    def write(self, vals):
        """Providers and drivers may not set the status directly (statusbar/RPC
        writes): status changes must go through the action buttons, and pickup /
        drop-off completion additionally requires the customer's code.

        The internal action methods write through order.sudo(), so this guard
        does not interfere with them: `env.su` is the discriminator. Note that
        _is_logspace_driver_user() deliberately ignores env.su (the driver
        portal controller loads orders with sudo() but must still authorize
        against the real session user), so the sudo check has to live here
        rather than inside it. A caller cannot set env.su over RPC - only
        server-side sudo() can - so this is not spoofable from the portal.
        """
        if 'logspace_state' in vals and not self.env.su and (
            self._is_logspace_provider_user() or self._is_logspace_driver_user()
        ):
            raise UserError(_(
                'You cannot change the order status directly. Use the status '
                'buttons; pickup and drop-off completion require the '
                "customer's verification code."
            ))
        # Remember who the driver was so the assignment email fires only when it
        # actually changes to someone new.
        previous_drivers = {}
        if 'logspace_driver_id' in vals:
            previous_drivers = {o.id: o.logspace_driver_id.id for o in self}
        # Remember the status so the status-change emails fire only on a real
        # transition, not on every write that happens to carry the key.
        previous_logspace_states = {}
        if 'logspace_state' in vals:
            previous_logspace_states = {o.id: o.logspace_state for o in self}
        res = super(SaleOrder, self).write(vals)
        if 'logspace_customer_rating' in vals:
            provider_ids = self.mapped('logspace_provider_id')
            if provider_ids:
                provider_ids._compute_logspace_rating()
        for order in self:
            if order.id in previous_logspace_states:
                order._notify_logspace_status_change(
                    previous_logspace_states[order.id],
                )
        if previous_drivers:
            for order in self:
                new_driver = order.logspace_driver_id.id
                if new_driver and new_driver != previous_drivers.get(order.id):
                    order._notify_driver_assigned()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Set the provider salesperson without exposing verification codes on drafts."""
        for vals in vals_list:
            if vals.get('is_logspace_order'):
                # Auto-set user_id (salesperson) from provider if not provided
                if not vals.get('user_id') and vals.get('logspace_provider_id'):
                    provider = self.env['res.partner'].browse(vals['logspace_provider_id'])
                    if provider.user_ids:
                        vals['user_id'] = provider.user_ids[0].id
        return super(SaleOrder, self).create(vals_list)
