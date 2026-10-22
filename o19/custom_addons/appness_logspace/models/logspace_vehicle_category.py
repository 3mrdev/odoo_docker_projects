# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LogspaceVehicleCategory(models.Model):
    """Logspace Vehicle Categories - groups vehicle types (Light, Medium, ...)"""
    _name = 'logspace.vehicle.category'
    _description = 'Logspace Vehicle Category'
    _order = 'sequence, name'

    name = fields.Char(string='Category', required=True, translate=True)
    code = fields.Char(string='Category Code', required=True, index=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True, string='Active')

    vehicle_type_ids = fields.One2many(
        'logspace.vehicle.type',
        'category_id',
        string='Vehicle Types'
    )

    _code_unique = models.Constraint('unique(code)', 'Vehicle category code must be unique!')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code'):
                vals['code'] = vals['code'].lower().replace(' ', '_')
        return super(LogspaceVehicleCategory, self).create(vals_list)
