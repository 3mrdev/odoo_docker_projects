# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    """Extend sales.order for Logspace bookings"""
    _inherit = 'sale.order'

    # Logspace Provider Fields
    logspace_provider_id = fields.Many2one('res.partner',
                                            string='Logspace Provider',
                                            domain=[('is_provider', '=', True), ('state', '=', 'approved')],
                                            index=True,
                                            help='Assigned logistics provider')
    logspace_vehicle_id = fields.Many2one('logspace.vehicle',
                                           string='Assigned Vehicle',
                                           domain="[('provider_id', '=', logspace_provider_id), ('is_active', '=', True)]")
    driver_id = fields.Many2one('res.partner', string='Driver',
                               help='Assigned driver contact')
    driver_phone = fields.Char(string='Driver Phone',
                                related='driver_id.phone', readonly=False)

    # Route Information
    pickup_address = fields.Text(string='Pickup Address', required=True)
    pickup_zone_id = fields.Many2one('logspace.zone', string='Pickup Zone')
    dropoff_address = fields.Text(string='Dropoff Address', required=True)
    dropoff_zone_id = fields.Many2one('logspace.zone', string='Dropoff Zone')
    scheduled_date = fields.Datetime(string='Scheduled Pickup Date')
    delivery_date = fields.Datetime(string='Actual Delivery Date')
    estimated_distance_km = fields.Float(string='Estimated Distance (km)')

    # Item Details
    item_description = fields.Text(string='Item Description',
                                    help='What is being moved')
    estimated_weight_kg = fields.Integer(string='Estimated Weight (kg)')
    item_quantity = fields.Integer(string='Number of Items', default=1)
    item_length_cm = fields.Integer(string='Length (cm)')
    item_width_cm = fields.Integer(string='Width (cm)')
    item_height_cm = fields.Integer(string='Height (cm)')
    special_instructions = fields.Text(string='Special Instructions')

    # Logspace State (for logistics tracking)
    logspace_state = fields.Selection([
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('driver_assigned', 'Driver Assigned'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ], string='Logspace Status', default='pending', index=True,
       tracking=True)

    # Add-ons
    logspace_addon_ids = fields.Many2many('logspace.addon',
                                          string='Selected Add-ons')

    # Timeline
    timeline_ids = fields.One2many('logspace.order.timeline', 'order_id',
                                   string='Tracking Timeline',
                                   readonly=True)

    # Related Records
    logspace_rating_ids = fields.One2many('logspace.rating', 'order_id',
                                          string='Logspace Ratings')
    logspace_refund_ids = fields.One2many('logspace.refund', 'order_id',
                                          string='Refund Requests')
    logspace_ticket_ids = fields.One2many('logspace.ticket', 'order_id',
                                          string='Support Tickets')

    def action_logspace_confirm(self):
        """Confirm booking and create timeline event"""
        for order in self:
            order.logspace_state = 'confirmed'
            self.env['logspace.order.timeline'].create({
                'order_id': order.id,
                'event_type': 'confirmed',
                'description': 'Booking confirmed and payment received',
            })

    def action_assign_driver(self):
        """Assign driver and create timeline event"""
        for order in self:
            order.logspace_state = 'driver_assigned'
            self.env['logspace.order.timeline'].create({
                'order_id': order.id,
                'event_type': 'driver_assigned',
                'description': f'Driver assigned: {order.driver_id.name}',
            })

    def action_start_transit(self):
        """Start transit and create timeline event"""
        for order in self:
            order.logspace_state = 'in_transit'
            self.env['logspace.order.timeline'].create({
                'order_id': order.id,
                'event_type': 'in_transit',
                'description': 'Driver in transit to destination',
            })

    def action_mark_delivered(self):
        """Mark delivered and create timeline event"""
        for order in self:
            order.logspace_state = 'delivered'
            order.delivery_date = fields.Datetime.now()
            self.env['logspace.order.timeline'].create({
                'order_id': order.id,
                'event_type': 'delivered',
                'description': 'Delivered successfully',
            })


class LogspaceOrderTimeline(models.Model):
    """Order Timeline Events - Tracking History"""
    _name = 'logspace.order.timeline'
    _description = 'Logspace Order Timeline'
    _order = 'sequence, event_time'

    order_id = fields.Many2one('sale.order', string='Order',
                                required=True, ondelete='cascade',
                                index=True)
    event_type = fields.Selection([
        ('booked', 'Booked'),
        ('confirmed', 'Confirmed'),
        ('driver_assigned', 'Driver Assigned'),
        ('pickup', 'Pickup Started'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ], string='Event Type', required=True)
    event_time = fields.Datetime(string='Event Time',
                                  default=lambda self: fields.Datetime.now())
    description = fields.Char(string='Description')
    location = fields.Char(string='Location')
    is_current = fields.Boolean(string='Current Status', default=False)
    sequence = fields.Integer(string='Sequence', default=10)

    # Related fields
    order_state = fields.Selection(related='order_id.logspace_state',
                                    string='Order State')
