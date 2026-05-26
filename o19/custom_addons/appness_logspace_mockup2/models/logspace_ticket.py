# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LogspaceTicket(models.Model):
    """Logspace Support Ticket - Customer Support System"""
    _name = 'logspace.ticket'
    _description = 'Logspace Support Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'

    name = fields.Char(string='Ticket Number', required=True,
                       index=True, readonly=True, default='New')
    category = fields.Selection([
        ('booking_issue', 'Booking Issue'),
        ('payment_problem', 'Payment Problem'),
        ('driver_complaint', 'Driver Complaint'),
        ('vehicle_issue', 'Vehicle Issue'),
        ('refund_request', 'Refund Request'),
        ('technical_support', 'Technical Support'),
        ('general_inquiry', 'General Inquiry'),
    ], string='Category', required=True)
    subject = fields.Char(string='Subject', required=True)
    description = fields.Text(string='Description', required=True)

    # Related Records
    order_id = fields.Many2one('sale.order', string='Related Order',
                                index=True, help='Optional linked order')
    customer_id = fields.Many2one('res.partner', string='Customer',
                                   index=True,
                                   default=lambda self: self.env.user.partner_id)
    provider_id = fields.Many2one('res.partner', string='Provider',
                                   related='order_id.logspace_provider_id',
                                   store=True, readonly=True)
    attachments = fields.Many2many('ir.attachment', string='Attachments')

    # Assignment & Priority
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Priority', default='medium', required=True, index=True)
    assigned_to_id = fields.Many2one('res.users', string='Assigned To',
                                      index=True,
                                      domain="[('share', '=', False)]")

    # Workflow
    state = fields.Selection([
        ('new', 'New'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('waiting_customer', 'Waiting for Customer'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('escalated', 'Escalated'),
    ], string='Status', default='new', required=True,
       tracking=True, index=True)

    create_date = fields.Datetime(string='Created', readonly=True)
    resolved_date = fields.Datetime(string='Resolved Date')
    resolution_notes = fields.Text(string='Resolution Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'logspace.ticket') or 'New'
        return super(LogspaceTicket, self).create(vals_list)

    def action_assign(self, user_id=None):
        """Assign ticket to user"""
        for ticket in self:
            if ticket.state not in ['new', 'assigned', 'in_progress']:
                raise UserError(_('Ticket cannot be assigned in this state.'))
            vals = {'state': 'assigned'}
            if user_id:
                vals['assigned_to_id'] = user_id
            ticket.write(vals)

    def action_start_progress(self):
        """Start working on ticket"""
        for ticket in self:
            if ticket.state not in ['new', 'assigned']:
                raise UserError(_('Ticket must be assigned to start progress.'))
            ticket.state = 'in_progress'

    def action_wait_customer(self):
        """Waiting for customer response"""
        for ticket in self:
            if ticket.state not in ['assigned', 'in_progress']:
                raise UserError(_('Ticket must be in progress.'))
            ticket.state = 'waiting_customer'

    def action_resolve(self, notes=None):
        """Mark as resolved"""
        for ticket in self:
            if ticket.state in ['resolved', 'closed']:
                raise UserError(_('Ticket is already resolved.'))
            ticket.write({
                'state': 'resolved',
                'resolved_date': fields.Datetime.now(),
                'resolution_notes': notes or '',
            })

    def action_close(self):
        """Close ticket"""
        for ticket in self:
            if ticket.state != 'resolved':
                raise UserError(_('Ticket must be resolved before closing.'))
            ticket.state = 'closed'

    def action_escalate(self):
        """Escalate ticket"""
        for ticket in self:
            if ticket.state == 'closed':
                raise UserError(_('Closed tickets cannot be escalated.'))
            ticket.write({
                'state': 'escalated',
                'priority': 'high' if ticket.priority != 'urgent' else 'urgent',
            })

    def action_reopen(self):
        """Reopen closed/resolved ticket"""
        for ticket in self:
            if ticket.state not in ['resolved', 'closed']:
                raise UserError(_('Ticket is not closed.'))
            ticket.state = 'in_progress'
