# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class LogspaceZone(models.Model):
    """Logspace Service Zones - Master Data"""
    _name = 'logspace.zone'
    _description = 'Logspace Zone'
    _order = 'name'

    name = fields.Char(string='Zone Name', required=True, translate=True)
    code = fields.Char(string='Zone Code', required=True, index=True)
    city = fields.Char(string='City', required=True)
    region = fields.Char(string='Region/State')
    country_id = fields.Many2one('res.country', string='Country')
    active = fields.Boolean(default=True, string='Active')

    _code_unique = models.Constraint('unique(code)', 'Zone code must be unique!')

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-uppercase the code"""
        for vals in vals_list:
            if vals.get('code'):
                vals['code'] = vals['code'].upper()
        return super(LogspaceZone, self).create(vals_list)

    def write(self, vals):
        """Auto-uppercase the code"""
        if vals.get('code'):
            vals['code'] = vals['code'].upper()
        return super(LogspaceZone, self).write(vals)
