# -*- coding: utf-8 -*-

from odoo import models, fields


class HelpdeskTicket(models.Model):
    """Extend helpdesk.ticket for Logspace integration"""
    _inherit = 'helpdesk.ticket'

    # =========================================================================
    # Logspace Identification
    # =========================================================================
    is_logspace_ticket = fields.Boolean(
        string='Logspace Ticket',
        default=False,
        help='Check if this ticket is related to Logspace logistics service',
        index=True
    )

    # =========================================================================
    # Related Order
    # =========================================================================
    logspace_order_id = fields.Many2one(
        'sale.order',
        string='Related Order',
        domain=[('is_logspace_order', '=', True)],
        help='Linked Logspace order if applicable',
        index=True
    )

    # =========================================================================
    # Logspace-specific Category
    # =========================================================================
    logspace_ticket_type = fields.Selection([
        ('booking', 'Booking Issue'),
        ('payment', 'Payment Issue'),
        ('delivery', 'Delivery Problem'),
        ('driver', 'Driver Complaint'),
        ('refund', 'Refund Request'),
        ('vehicle', 'Vehicle Issue'),
        ('other', 'Other'),
    ], string='Ticket Category',
       help='Type of Logspace-related issue',
       index=True
    )

    # =========================================================================
    # Customer Info (if guest order)
    # =========================================================================
    guest_email = fields.Char(
        string='Guest Email',
        related='logspace_order_id.guest_email',
        store=True,
        readonly=True,
        help='Email from guest order if applicable'
    )

    # =========================================================================
    # Related Records
    # =========================================================================
    logspace_provider_id = fields.Many2one(
        'res.partner',
        string='Provider',
        related='logspace_order_id.logspace_provider_id',
        store=True,
        readonly=True,
        help='Provider involved in this ticket'
    )

    # =========================================================================
    # Visibility Flag
    # =========================================================================
    show_to_customer = fields.Boolean(
        string='Visible to Customer',
        default=True,
        help='If checked, customer can see this ticket in their portal'
    )
