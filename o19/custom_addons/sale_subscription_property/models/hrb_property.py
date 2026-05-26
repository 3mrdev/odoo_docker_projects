# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError

class Property(models.Model):
    _name = 'hrb.property'
    _description = 'Property Information'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    show_properties_features = fields.Boolean(related='company_id.show_properties_features',store=True)
    name = fields.Char(string='Name', required=True,translate=True)
    sequence_number = fields.Char(string='Sequence Number', readonly=True)
    date = fields.Date(string='Date', tracking=True)
    valuation = fields.Float(string='Valuation')
    land_number = fields.Char(string='Land Number')
    donor_terms_and_conditions = fields.Html(string='Donor Terms and Conditions')
    notes = fields.Html(string='Notes')
    address_location_details_link = fields.Char(string='Address/Location Details Link')
    address_location_details_id = fields.Many2one('res.partner', string='Address/Location Details')
    property_type_id = fields.Many2one('hrb.property.type', string='Property Type')
    responsible_id = fields.Many2one('res.partner', string='Responsible')
    responsible_invoice_address_updated = fields.Date(string='Invoice Address Updated', compute='_compute_responsible_invoice_address',store=True)
    unit_ids = fields.One2many('hrb.property.unit', 'property_id', string='Units')
    tag_ids = fields.Many2many('crm.tag', string='Tags')
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('sold', 'Sold'),
    ], string='Status', default='draft')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one('res.country.state')
    country_id = fields.Many2one('res.country')
    country_enforce_cities = fields.Boolean(related='country_id.enforce_cities')
    city_id = fields.Many2one('res.city', string='City')
    area_id = fields.Many2one('res.area', string='Area')

    invoices = fields.One2many('account.move', 'property_id', string='Invoices')
    invoices_count = fields.Integer(string='Invoices Count', compute='_compute_invoices_count')
    subscriptions = fields.One2many('sale.order', 'property_id', string='Subscriptions')
    subscriptions_count = fields.Integer(string='Subscriptions Count', compute='_compute_subscriptions_count')

    @api.depends("responsible_id")
    def _compute_responsible_invoice_address(self):
        for property in self:
            for unit in property.unit_ids:
                for subscription in unit.subscription_ids:
                    if subscription.state == 'sale':
                        if property.responsible_id:
                            subscription.partner_invoice_id = property.responsible_id
                            subscription.partner_shipping_id = property.responsible_id
                        # else:
                        #     subscription.partner_invoice_id = subscription.partner_id
                        #     subscription.partner_shipping_id = subscription.partner_id

            property.responsible_invoice_address_updated = fields.Date.today()
    
    @api.depends('invoices')
    def _compute_invoices_count(self):
        for property in self:
            property.invoices_count = len(property.invoices)

    @api.depends('subscriptions')
    def _compute_subscriptions_count(self):
        for property in self:
            property.subscriptions_count = len(property.subscriptions)

    def action_view_subscriptions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Subscriptions',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
        }

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
        }

    def action_view_units(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Units',
            'res_model': 'hrb.property.unit',
            'view_mode': 'list,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
        }

    units_total_rent = fields.Float(string='Total Rent', compute='_compute_unit_counts')
    unit_count = fields.Integer(string='Unit Count', compute='_compute_unit_counts')
    free_unit_count = fields.Integer(string='Free Units', compute='_compute_unit_counts')
    rented_unit_count = fields.Integer(string='Rented Units', compute='_compute_unit_counts')
    maintenance_unit_count = fields.Integer(string='Maintenance Units', compute='_compute_unit_counts')

    @api.depends('unit_ids.status')
    def _compute_unit_counts(self):
        for property in self:
            property.unit_count = len(property.unit_ids)
            property.units_total_rent = sum(property.unit_ids.mapped('price'))
            property.free_unit_count = len(property.unit_ids.filtered(lambda u: u.status == 'free'))
            property.rented_unit_count = len(property.unit_ids.filtered(lambda u: u.status == 'under_rent'))
            property.maintenance_unit_count = len(property.unit_ids.filtered(lambda u: u.status == 'under_maintenance'))
   
    def action_submit(self):
        for property in self:
            property.write({'status': 'in_progress'})
            
            for unit in property.unit_ids:
                rented = False
                for subscription in unit.subscription_ids:
                    if subscription.state == 'sale':
                        rented = True
                        break
                if rented:
                    unit.action_set_under_rent()
                else:
                    unit.action_set_free()

    def action_hold(self):
        for property in self:
            property.write({'status': 'on_hold'})
            for unit in property.unit_ids:
                unit.action_hold()
            
    def action_sell(self):
        for property in self:
            property.write({'status': 'sold'})
            for unit in property.unit_ids:
                unit.action_sell()

    def action_reset_to_draft(self):
        for property in self:
            property.write({'status': 'draft'})

    def action_view_units(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'{self.name} - Units',
            'res_model': 'hrb.property.unit',
            'view_mode': 'list,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
        }
    
    @api.model_create_multi
    def create(self, vals):
        rec = super(Property, self).create(vals)
        
        if not rec.sequence_number:
            rec.sequence_number = self.env['ir.sequence'].next_by_code('hrb.property')
        
        if not rec.analytic_account_id:
            # TODO
            default_analytic_plan_property = self.env['ir.config_parameter'].sudo().get_param(
            'sale_subscription_property.default_analytic_plan_property', default=False)
            if default_analytic_plan_property:
                analytic_plan = self.env['account.analytic.plan'].search([('id', '=', int(default_analytic_plan_property))])
                if not analytic_plan:
                    analytic_plan = self.env['account.analytic.plan'].create({
                        'name': str(default_analytic_plan_property),
                    })
                analytic_account_id = self.env['account.analytic.account'].create({
                    'name': rec.name,
                    'code': rec.sequence_number,
                    'company_id': rec.company_id.id,
                    'plan_id': analytic_plan.id,
                })
                rec.analytic_account_id = analytic_account_id.id
            else:
                raise UserError(_("Please configure the default analytic plan for properties in the settings."))

        return rec

    def unlink(self):
        for property in self:
            if property.status != 'draft':
                raise UserError(_("You can only delete a Property that is in draft state."))
            elif property.status == 'draft':
                if property.unit_ids:
                    raise UserError(_("You cannot delete a Property that has units."))
                elif property.invoices:
                    raise UserError(_("You cannot delete a Property that has invoices."))
                elif property.subscriptions:
                    raise UserError(_("You cannot delete a Property that has subscriptions."))
        return super(Property, self).unlink()