# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class LogspaceAddon(models.Model):
    """Logspace Service Add-ons - Master Data"""
    _name = 'logspace.addon'
    _description = 'Logspace Service Add-on'
    _order = 'sequence, name'

    name = fields.Char(string='Add-on Name', required=True, translate=True)
    code = fields.Char(string='Add-on Code', required=True, index=True)
    description = fields.Text(string='Description', translate=True,
                              help='Shown on vendor page to describe the add-on')
    price = fields.Float(string='Base Price', required=True, default=0.0)
    price_type = fields.Selection([
        ('fixed', 'Fixed Price'),
        ('per_km', 'Per Kilometer'),
        ('per_hour', 'Per Hour'),
        ('per_item', 'Per Item'),
    ], string='Pricing Type', default='fixed', required=True)
    icon = fields.Char(string='Icon Class', default='fa-plus',
                       help='FontAwesome icon class')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True, string='Active')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                   default=lambda self: self.env.company.currency_id)

    _code_unique = models.Constraint('unique(code)', 'Add-on code must be unique!')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code'):
                vals['code'] = vals['code'].lower().replace(' ', '_')
        return super(LogspaceAddon, self).create(vals_list)
