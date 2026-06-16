# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class JizWaqfUnit(models.Model):
    _name = 'jiz.waqf.unit'
    _description = 'Waqf Unit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    internal_reference = fields.Char(string='Internal Reference')
    waqf_id = fields.Many2one('jiz.waqf', string='Waqf', required=True, ondelete='cascade')
    sequence_number = fields.Char(string='Sequence Number', readonly=True)
    address_link = fields.Char(string='Address Link', related='waqf_id.address_location_details_link')
    address_location_details_id = fields.Many2one('res.partner', string='Address/Location Details', related='waqf_id.address_location_details_id')
    status = fields.Selection([
        ('free', 'Free'),
        ('under_rent', 'Under Rent'),
        ('under_maintenance', 'Under Maintenance'),
        ('on_hold', 'On Hold'),
        ('sold', 'Sold'),
    ], string='Status', default='free')
    tenant_id = fields.Many2one('res.partner', string='Tenant',tracking=True)
    responsible_id = fields.Many2one('res.partner', string='Responsible', related='waqf_id.responsible_id', store=True)
    # invoice_address_id = fields.Many2one('res.partner', string='Invoice Address', related='waqf_id.invoice_address_id', store=True)
    subscription_ids = fields.One2many('sale.order', 'waqf_unit_id', string='Subscriptions')
    subscription_count = fields.Integer(string='Subscription Count', compute='_compute_subscription_count')
    product_id = fields.Many2one('product.product', string='Product')
    price = fields.Float(string='Price')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account (Legacy)')
    analytic_distribution = fields.Json(string='Analytic Distribution')
    analytic_precision = fields.Integer(default=2)

    street = fields.Char(related='waqf_id.street')
    street2 = fields.Char(related='waqf_id.street2')
    zip = fields.Char(related='waqf_id.zip')
    city = fields.Char(related='waqf_id.city')
    state_id = fields.Many2one('res.country.state', related='waqf_id.state_id')
    country_id = fields.Many2one('res.country', related='waqf_id.country_id')
    country_enforce_cities = fields.Boolean(related='country_id.enforce_cities')
    city_id = fields.Many2one('res.city', string='City', related='waqf_id.city_id')
    area_id = fields.Many2one('res.area', string='Area', related='waqf_id.area_id')

    @api.depends('subscription_ids')
    def _compute_subscription_count(self):
        for unit in self:
            unit.subscription_count = len(unit.subscription_ids)

    def action_view_subscriptions(self):
        self.ensure_one()
        analytic_distribution = self.analytic_distribution or {}
        return {
            'type': 'ir.actions.act_window',
            'name': 'Subscriptions',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('waqf_unit_id', '=', self.id)],
            'context': {
                'default_waqf_unit_id': self.id,
                # 'default_partner_id': self.tenant_id.id,
                'default_partner_invoice_id': self.responsible_id.id or False,
                'default_partner_shipping_id': self.responsible_id.id or False,
                'default_order_line': [(0, 0, {
                    'product_id': self.product_id.id,
                    'product_uom_qty': 1,
                    'price_unit': self.price,
                    'analytic_distribution': analytic_distribution,
                })],
            }
        }

    def action_create_rent(self):
        self.ensure_one()

        # if not self.tenant_id:
        #     raise UserError(_("Tenant is required to create a rent."))

        analytic_distribution = self.analytic_distribution or {}

        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Subscription',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'context': {
                'default_waqf_unit_id': self.id,
                # 'default_partner_id': self.tenant_id.id,
                'default_partner_invoice_id': self.responsible_id.id or False,
                'default_partner_shipping_id': self.responsible_id.id or False,
                'default_order_line': [(0, 0, {
                    'product_id': self.product_id.id,
                    'product_uom_qty': 1,
                    'price_unit': self.price,
                    'analytic_distribution': analytic_distribution,
                })],
            }
        }

    @api.depends('waqf_id.name', 'sequence_number', 'internal_reference')
    def _compute_name(self):
        for unit in self:
            name = unit.sequence_number
            if unit.internal_reference:
                name = f'[{unit.internal_reference}] {name}'
            if unit.waqf_id:
                name = f'{unit.waqf_id.name} - {name}'
            unit.name = name

    def action_set_free(self):
        self.write({'status': 'free'})

    def action_set_under_rent(self):
        self.write({'status': 'under_rent'})
        for subscription in self.subscription_ids:
            if subscription.subscription_state == '4_paused':
                subscription.resume_subscription()

    def action_set_under_maintenance(self):
        self.write({'status': 'under_maintenance'})

    def action_hold(self):
        self.write({'status': 'on_hold'})
        for subscription in self.subscription_ids:
            if subscription.subscription_state == '3_progress':
                subscription.pause_subscription()

    def action_sell(self):
        self.write({'status': 'sold'})
        close_reason_id = self.env['sale.order.close.reason'].search([('name', '=', 'Property Sold')], limit=1)
        
        if not close_reason_id:
            close_reason_id = self.env['sale.order.close.reason'].create({'name': 'Property Sold'})

        for subscription in self.subscription_ids:
            if subscription.subscription_state == '3_progress':
                subscription.close_reason_id = close_reason_id.id
                subscription.set_close(close_reason_id=close_reason_id.id)
    
    @api.model_create_multi
    def create(self, vals):
        rec = super(JizWaqfUnit, self).create(vals)

        if not rec.sequence_number:
            rec.sequence_number = self.env['ir.sequence'].next_by_code('jiz.waqf.unit')

        if not rec.analytic_distribution and rec.waqf_id.analytic_distribution:
            rec.analytic_distribution = rec.waqf_id.analytic_distribution

        return rec

    def unlink(self):
        for waqf in self:
            if waqf.status != 'free':
                raise UserError(_("It cannot be deleted while it is under rent or on hold."))
            elif waqf.status == 'free':
                if waqf.subscription_ids:
                    raise UserError(_("You cannot delete a Waqf that has subscriptions."))

        return super(JizWaqfUnit, self).unlink()