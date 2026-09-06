# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


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
        ('payment_received', 'Payment Received'),
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
