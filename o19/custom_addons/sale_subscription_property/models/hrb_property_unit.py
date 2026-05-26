# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PropertyUnit(models.Model):
    _name = 'hrb.property.unit'
    _description = 'Property Unit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    internal_reference = fields.Char(string='Internal Reference')
    property_id = fields.Many2one('hrb.property', string='Property', required=True, ondelete='cascade')
    sequence_number = fields.Char(string='Sequence Number', readonly=True)
    address_link = fields.Char(string='Address Link', related='property_id.address_location_details_link')
    address_location_details_id = fields.Many2one('res.partner', string='Address/Location Details', related='property_id.address_location_details_id')
    status = fields.Selection([
        ('free', 'Free'),
        ('under_rent', 'Under Rent'),
        ('under_maintenance', 'Under Maintenance'),
        ('on_hold', 'On Hold'),
        ('sold', 'Sold'),
    ], string='Status', default='free')
    tenant_id = fields.Many2one('res.partner', string='Tenant',tracking=True)
    responsible_id = fields.Many2one('res.partner', string='Responsible', related='property_id.responsible_id', store=True)
    unit_type_id = fields.Many2one('hrb.property.type', string='Unit Type')
    subscription_ids = fields.One2many('sale.order', 'property_unit_id', string='Subscriptions')
    subscription_count = fields.Integer(string='Subscription Count', compute='_compute_subscription_count')
    product_id = fields.Many2one('product.product', string='Product')
    price = fields.Float(string='Price')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    tag_ids = fields.Many2many('crm.tag', string='Tags')

    street = fields.Char(related='property_id.street')
    street2 = fields.Char(related='property_id.street2')
    zip = fields.Char(related='property_id.zip')
    city = fields.Char(related='property_id.city')
    state_id = fields.Many2one('res.country.state', related='property_id.state_id')
    country_id = fields.Many2one('res.country', related='property_id.country_id')
    country_enforce_cities = fields.Boolean(related='country_id.enforce_cities')
    city_id = fields.Many2one('res.city', string='City', related='property_id.city_id')
    area_id = fields.Many2one('res.area', string='Area', related='property_id.area_id')
    company_id = fields.Many2one('res.company',related='property_id.company_id',readonly=False,default=lambda self: self.env.company.id)
    show_properties_features = fields.Boolean(related='company_id.show_properties_features',store=True)

    @api.depends('subscription_ids')
    def _compute_subscription_count(self):
        for unit in self:
            unit.subscription_count = len(unit.subscription_ids)

    def action_view_subscriptions(self):
        self.ensure_one()

        analytic_distribution = {}
        if self.analytic_account_id:
            analytic_distribution = {str(self.analytic_account_id.id): 100}
        else:
            if self.property_id.analytic_account_id:
                analytic_distribution = {str(self.property_id.analytic_account_id.id): 100}
            else:
                analytic_distribution = {}

        context = {
            'default_property_unit_id': self.id,
            'default_order_line': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty': 1,
                'price_unit': self.price,
                'analytic_distribution': analytic_distribution,
            })],
        }

        if self.responsible_id:
            context['default_partner_invoice_id'] = self.responsible_id.id
            context['default_partner_shipping_id'] = self.responsible_id.id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Subscriptions',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('property_unit_id', '=', self.id)],
            'context': context
        }

    def action_create_rent(self):
        self.ensure_one()

        analytic_distribution = {}
        if self.analytic_account_id:
            analytic_distribution = {str(self.analytic_account_id.id): 100}
        else:
            if self.property_id.analytic_account_id:
                analytic_distribution = {str(self.property_id.analytic_account_id.id): 100}
            else:
                analytic_distribution = {}

        context = {
            'default_property_unit_id': self.id,
            'default_order_line': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty': 1,
                'price_unit': self.price,
                'analytic_distribution': analytic_distribution,
            })],
        }

        if self.responsible_id:
            context['default_partner_invoice_id'] = self.responsible_id.id
            context['default_partner_shipping_id'] = self.responsible_id.id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Subscription',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'context': context
        }

    @api.depends('property_id.name', 'sequence_number', 'internal_reference')
    def _compute_name(self):
        for unit in self:
            name = unit.sequence_number
            if unit.internal_reference:
                name = f'[{unit.internal_reference}] {name}'
            if unit.property_id:
                name = f'{unit.property_id.name} - {name}'
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
        rec = super(PropertyUnit, self).create(vals)

        if not rec.sequence_number:
            rec.sequence_number = self.env['ir.sequence'].next_by_code('hrb.property.unit')
        return rec

    def generate_sequence_number(self):
        for property in self:
            if not property.sequence_number:
                property.sequence_number = self.env['ir.sequence'].next_by_code('hrb.property.unit')

    def unlink(self):
        for property in self:
            if property.status != 'free':
                raise UserError(_("It cannot be deleted while it is under rent or on hold."))
            elif property.status == 'free':
                if property.subscription_ids:
                    raise UserError(_("You cannot delete a property that has subscriptions."))

        return super(PropertyUnit, self).unlink()