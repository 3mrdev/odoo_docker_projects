# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class LogspaceZone(models.Model):
    """Logspace Service Zones - Master Data"""
    _name = 'logspace.zone'
    _description = 'Logspace Zone'
    _order = 'name'

    name = fields.Char(string='Zone Name', required=True, translate=True)
    code = fields.Char(string='Zone Code', required=True, index=True)
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
        ('country', 'Country'),
        ('governorate', 'Governorate'),
        ('city', 'City'),
        ('district', 'District'),
        ('area', 'Area'),
    ], string='Zone Type', default='city',
       help='Classification level of this zone')

    # Geolocation
    lat = fields.Float(string='Latitude', digits=(16, 10))
    lng = fields.Float(string='Longitude', digits=(16, 10))

    _code_unique = models.Constraint('unique(code)', 'Zone code must be unique!')

    def _get_zone_hierarchy_ids(self):
        """Return self + all ancestors + all descendants for bidirectional search.

        This allows:
        - District search → finds parent city vehicles/prices (walk UP)
        - City search → finds vehicles/prices in child districts (walk DOWN)
        """
        self.ensure_one()
        zone_ids = {self.id}

        # Walk UP to collect all ancestors
        current = self
        while current.parent_id:
            zone_ids.add(current.parent_id.id)
            current = current.parent_id

        # Walk DOWN to collect all descendants (BFS)
        zones_to_check = list(self.child_ids)
        while zones_to_check:
            zone = zones_to_check.pop()
            zone_ids.add(zone.id)
            zones_to_check.extend(zone.child_ids)

        return list(zone_ids)

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

    @api.depends('name', 'parent_id', 'parent_id.name')
    def _compute_display_name(self):
        """Override display name to show full hierarchical address path.

        Walks up the parent chain to build the full path. If a country-type
        zone exists at the top of the hierarchy, it appears naturally.
        """
        for zone in self:
            parts = []
            current = zone
            # Walk up the parent chain
            while current:
                if current.name and current.name not in parts:
                    parts.append(current.name)
                current = current.parent_id
            zone.display_name = ", ".join(parts)
