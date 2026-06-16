# -*- coding: utf-8 -*-

from odoo import models, fields, api
import random


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
        domain="[('is_company', '=', False)]"
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
       default='order_received',
       tracking=True,
       index=True,
       help='Current status of the logistics order'
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
    # Payment (Future Paymob Integration)
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
    ], string='Payment Method', default='cod')
    transaction_ref = fields.Char(
        string='Transaction Reference',
        help='Payment gateway transaction reference'
    )

    # =========================================================================
    # Related Records
    # =========================================================================
    logspace_rating_ids = fields.One2many(
        'logspace.rating',
        'order_id',
        string='Logspace Ratings'
    )
    logspace_refund_ids = fields.One2many(
        'logspace.refund',
        'order_id',
        string='Refund Requests'
    )
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
        string='Tickets',
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

    logspace_rating_ids = fields.One2many(
        'logspace.rating',
        'order_id',
        string='Ratings'
    )
    logspace_rating_count = fields.Integer(
        string='Ratings',
        compute='_compute_logspace_counts'
    )

    @api.depends('logspace_ticket_ids', 'logspace_refund_ids', 'logspace_rating_ids')
    def _compute_logspace_counts(self):
        """Compute counts for smart buttons"""
        for order in self:
            order.logspace_ticket_count = len(order.logspace_ticket_ids)
            order.logspace_refund_count = len(order.logspace_refund_ids)
            order.logspace_rating_count = len(order.logspace_rating_ids)

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

    def action_view_logspace_ratings(self):
        """Open ratings for this order"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "logspace.rating",
            "view_mode": "list,form",
            "domain": [('order_id', '=', self.id)],
            "context": {'default_order_id': self.id}
        }

    # =========================================================================
    # Actions - Workflow (Updated to match logspace_state field states)
    # =========================================================================

    def _create_timeline_event(self, event_type, description):
        """Helper to create timeline event"""
        self.env['logspace.order.timeline'].sudo().create({
            'order_id': self.id,
            'event_type': event_type,
            'description': description,
            'event_time': fields.Datetime.now(),
        })

    def action_logspace_confirm(self):
        """Confirm booking - sets state to order_received and generates pickup code"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            # Generate verification codes if not set
            if not order.verification_code_pickup:
                order.verification_code_pickup = f"{random.randint(1000, 9999)}"

            # Only set state if not already set
            if not order.logspace_state or order.logspace_state == 'order_received':
                order.logspace_state = 'order_received'

            # Create timeline event
            order._create_timeline_event('order_received', 'Order received and confirmed')

    def action_start_pickup(self):
        """Driver starts pickup - triggered when driver begins journey to pickup"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state != 'order_received':
                continue
            order.logspace_state = 'pickup_started'
            order._create_timeline_event('pickup_started', 'Pickup journey started')

    def action_vendor_arrived_pickup(self):
        """Vendor/driver arrived at pickup location"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state != 'pickup_started':
                continue
            order.logspace_state = 'vendor_arrived_pickup'
            order._create_timeline_event('vendor_arrived_pickup', 'Vendor arrived at pickup location')

    def action_pickup_addons(self):
        """Pickup add-ons performed (loading assistance, etc.)"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state != 'vendor_arrived_pickup':
                continue
            order.logspace_state = 'pickup_addons'
            order._create_timeline_event('pickup_addons', 'Pickup add-ons performed')

    def action_pickup_completed(self):
        """Pickup completed - items loaded, driver departs"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state not in ['pickup_started', 'vendor_arrived_pickup', 'pickup_addons']:
                continue
            order.logspace_state = 'pickup_completed'
            order._create_timeline_event('pickup_completed', 'Pickup completed, items loaded')

    def action_pre_dropoff_addons(self):
        """Pre-drop-off add-ons performed"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state != 'pickup_completed':
                continue
            order.logspace_state = 'pre_dropoff_addons'
            order._create_timeline_event('pre_dropoff_addons', 'Pre-drop-off add-ons performed')

    def action_arrived_destination(self):
        """Driver arrived at destination/dropoff"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state not in ['pickup_completed', 'pre_dropoff_addons']:
                continue
            # Generate dropoff code if not set
            if not order.verification_code_dropoff:
                order.verification_code_dropoff = f"{random.randint(1000, 9999)}"
            order.logspace_state = 'arrived_destination'
            order._create_timeline_event('arrived_destination', 'Arrived at destination')

    def action_dropoff_completed(self):
        """Drop-off completed - items delivered"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state != 'arrived_destination':
                continue
            order.logspace_state = 'dropoff_completed'
            order.delivery_date = fields.Datetime.now()
            order._create_timeline_event('dropoff_completed', 'Drop-off completed')

    def action_start_grace_period(self):
        """Start grace period after dropoff"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state != 'dropoff_completed':
                continue
            order.logspace_state = 'grace_period'
            order._create_timeline_event('grace_period', 'Grace period started')

    def action_complete_order(self):
        """Final order completion"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state not in ['dropoff_completed', 'grace_period']:
                continue
            order.logspace_state = 'order_completed'
            order._create_timeline_event('order_completed', 'Order fully completed')

            # Send order completion email
            try:
                template = self.env.ref('appness_logspace_mockup2.email_template_order_delivered')
                if template:
                    template.send_mail(order.id, force_send=True)
            except Exception:
                pass

    def action_cancel_logspace(self):
        """Cancel logistics order"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state in ['order_completed', 'dropoff_completed']:
                continue
            order.logspace_state = 'cancelled'
            order._create_timeline_event('cancelled', 'Order cancelled')

    def action_reset_logspace_to_draft(self):
        """Reset cancelled logistics order back to order_received"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state != 'cancelled':
                continue
            order.logspace_state = 'order_received'
            order._create_timeline_event('order_received', 'Order reset to received from cancelled')

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

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate verification codes and set salesperson for logspace orders"""
        for vals in vals_list:
            if vals.get('is_logspace_order'):
                if not vals.get('verification_code_pickup'):
                    vals['verification_code_pickup'] = f"{random.randint(1000, 9999)}"
                if not vals.get('verification_code_dropoff'):
                    vals['verification_code_dropoff'] = f"{random.randint(1000, 9999)}"
                # Auto-set user_id (salesperson) from provider if not provided
                if not vals.get('user_id') and vals.get('logspace_provider_id'):
                    provider = self.env['res.partner'].browse(vals['logspace_provider_id'])
                    if provider.user_ids:
                        vals['user_id'] = provider.user_ids[0].id
        return super(SaleOrder, self).create(vals_list)
