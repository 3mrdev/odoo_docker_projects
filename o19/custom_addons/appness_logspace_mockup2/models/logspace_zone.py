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
    state_id = fields.Many2one(
        'res.country.state', string='State/Governorate',
        domain="[('country_id', '=', country_id)]",
        help='Link to Odoo administrative state/governorate',
    )
    active = fields.Boolean(default=True, string='Active')
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description')

    # Hierarchy
    parent_id = fields.Many2one(
        'logspace.zone', string='Parent Zone',
        index=True, ondelete='set null',
        help='Parent zone (e.g. governorate for a city zone)',
    )
    child_ids = fields.One2many(
        'logspace.zone', 'parent_id', string='Child Zones',
    )

    # Classification
    zone_type = fields.Selection([
        ('governorate', 'Governorate'),
        ('city', 'City'),
        ('district', 'District'),
        ('area', 'Area'),
    ], string='Zone Type', default='city',
       help='Classification level of this zone')

    # Matching
    zip_codes = fields.Char(
        string='ZIP/Postal Codes',
        help='Comma-separated ZIP/postal code prefixes for automatic zone assignment',
    )

    lat = fields.Float(string='Latitude', digits=(16, 10))
    lng = fields.Float(string='Longitude', digits=(16, 10))

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
