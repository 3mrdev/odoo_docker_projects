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
    estimated_weight_kg = fields.Integer(
        string='Estimated Weight (kg)',
        help='Approximate total weight of items'
    )
    item_quantity = fields.Integer(
        string='Number of Items',
        default=1,
        help='How many items/pieces being transported'
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
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('driver_assigned', 'Driver Assigned'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ], string='Logspace Status',
       default='pending',
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
    # Actions - Workflow
    # =========================================================================
    def action_logspace_confirm(self):
        """Confirm booking and generate pickup verification code"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state != 'pending':
                continue

            # Generate verification codes if not set
            if not order.verification_code_pickup:
                order.verification_code_pickup = f"{random.randint(1000, 9999)}"

            order.logspace_state = 'confirmed'

            # Create timeline event
            self.env['logspace.order.timeline'].sudo().create({
                'order_id': order.id,
                'event_type': 'confirmed',
                'description': 'Booking confirmed',
            })

    def action_assign_driver(self):
        """Assign driver to order"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state != 'confirmed':
                continue
            order.logspace_state = 'driver_assigned'
            self.env['logspace.order.timeline'].sudo().create({
                'order_id': order.id,
                'event_type': 'driver_assigned',
                'description': f'Driver assigned: {order.logspace_driver_id.name or "N/A"}',
            })

    def action_start_transit(self):
        """Mark as in transit"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state not in ['confirmed', 'driver_assigned']:
                continue
            order.logspace_state = 'in_transit'
            self.env['logspace.order.timeline'].sudo().create({
                'order_id': order.id,
                'event_type': 'in_transit',
                'description': 'Driver in transit to destination',
            })

    def action_mark_delivered(self):
        """Mark as delivered - generate dropoff code if needed"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state != 'in_transit':
                continue

            # Generate dropoff code if not set
            if not order.verification_code_dropoff:
                order.verification_code_dropoff = f"{random.randint(1000, 9999)}"

            order.logspace_state = 'delivered'
            order.delivery_date = fields.Datetime.now()

            self.env['logspace.order.timeline'].sudo().create({
                'order_id': order.id,
                'event_type': 'delivered',
                'description': 'Delivered successfully',
            })

    def action_cancel_logspace(self):
        """Cancel logistics order"""
        for order in self.filtered(lambda o: o.is_logspace_order):
            if order.logspace_state in ['delivered']:
                continue
            order.logspace_state = 'cancelled'
            self.env['logspace.order.timeline'].sudo().create({
                'order_id': order.id,
                'event_type': 'cancelled',
                'description': 'Order cancelled',
            })

    # =========================================================================
    # Override Create
    # =========================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate verification codes for logspace orders"""
        for vals in vals_list:
            if vals.get('is_logspace_order'):
                if not vals.get('verification_code_pickup'):
                    vals['verification_code_pickup'] = f"{random.randint(1000, 9999)}"
                if not vals.get('verification_code_dropoff'):
                    vals['verification_code_dropoff'] = f"{random.randint(1000, 9999)}"
        return super(SaleOrder, self).create(vals_list)
