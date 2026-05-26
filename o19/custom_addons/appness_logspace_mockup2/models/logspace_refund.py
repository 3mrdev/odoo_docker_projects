# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError


class LogspaceRefund(models.Model):
    """Logspace Refund - Refund Request Management"""
    _name = 'logspace.refund'
    _description = 'Logspace Refund Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Refund Reference', required=True,
                       index=True, readonly=True, default='New')
    order_id = fields.Many2one('sale.order', string='Order', required=True,
                                ondelete='restrict', index=True)
    customer_id = fields.Many2one('res.partner', string='Customer',
                                   related='order_id.partner_id',
                                   store=True, readonly=True)
    provider_id = fields.Many2one('res.partner', string='Provider',
                                     related='order_id.logspace_provider_id',
                                     store=True, readonly=True)

    # Financial
    amount = fields.Float(string='Refund Amount', required=True,
                          default=0.0)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                   related='order_id.currency_id',
                                   readonly=True, store=True)

    # Request Details
    reason = fields.Selection([
        ('service_not_provided', 'Service Not Provided'),
        ('late_delivery', 'Late Delivery'),
        ('damaged_goods', 'Damaged Goods'),
        ('wrong_vehicle', 'Wrong Vehicle Type'),
        ('overcharged', 'Overcharged'),
        ('cancelled_by_provider', 'Cancelled by Provider'),
        ('other', 'Other'),
    ], string='Reason', required=True)
    details = fields.Text(string='Details', required=True)
    attachments = fields.Many2many('ir.attachment', string='Attachments')

    # Workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    ], string='Status', default='draft', required=True,
       tracking=True, index=True)

    submitted_date = fields.Datetime(string='Submitted Date')
    processed_date = fields.Datetime(string='Processed Date')
    processed_by_id = fields.Many2one('res.users', string='Processed By')
    rejection_reason = fields.Text(string='Rejection Reason')
    refund_method = fields.Selection([
        ('original_payment', 'Original Payment Method'),
        ('credit', 'Account Credit'),
        ('bank_transfer', 'Bank Transfer'),
    ], string='Refund Method', default='original_payment')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'logspace.refund') or 'New'
        return super(LogspaceRefund, self).create(vals_list)

    def action_submit(self):
        """Submit refund request"""
        for refund in self:
            if refund.state != 'draft':
                raise UserError(_('Only draft refunds can be submitted.'))
            refund.write({
                'state': 'submitted',
                'submitted_date': fields.Datetime.now(),
            })

    def action_review(self):
        """Move to under review"""
        for refund in self:
            if refund.state not in ['submitted', 'draft']:
                raise UserError(_('Refund must be submitted first.'))
            refund.state = 'under_review'

    def action_approve(self):
        """Approve refund"""
        for refund in self:
            if refund.state not in ['submitted', 'under_review']:
                raise UserError(_('Refund must be under review to approve.'))
            refund.state = 'approved'

    def action_reject(self, reason=None):
        """Reject refund"""
        for refund in self:
            if refund.state not in ['submitted', 'under_review', 'approved']:
                raise UserError(_('Refund cannot be rejected in this state.'))
            refund.write({
                'state': 'rejected',
                'rejection_reason': reason or '',
                'processed_by_id': self.env.user.id,
                'processed_date': fields.Datetime.now(),
            })

    def action_process(self):
        """Mark refund as processed (payment sent)"""
        for refund in self:
            if refund.state != 'approved':
                raise UserError(_('Only approved refunds can be processed.'))
            refund.write({
                'state': 'processed',
                'processed_by_id': self.env.user.id,
                'processed_date': fields.Datetime.now(),
            })
