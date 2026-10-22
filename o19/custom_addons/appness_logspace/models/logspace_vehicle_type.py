# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class LogspaceVehicleType(models.Model):
    """Logspace Vehicle Types - Master Data"""
    _name = 'logspace.vehicle.type'
    _description = 'Logspace Vehicle Type'
    _order = 'sequence, name'

    name = fields.Char(string='Vehicle Type', required=True, translate=True)
    code = fields.Char(string='Type Code', required=True, index=True)
    icon = fields.Char(string='Icon Class', default='fa-truck',
                       help='FontAwesome icon class, e.g., fa-truck')
    default_capacity_kg = fields.Integer(string='Default Capacity (kg)')
    default_capacity_cbm = fields.Float(string='Default Capacity (cbm)')
    dimensions = fields.Char(string='Dimensions (L x W x H cm)', help='e.g., 300x200x150 cm')
    category_id = fields.Many2one(
        'logspace.vehicle.category', string='Category',
        ondelete='restrict', index=True)
    description = fields.Text(string='Description', translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True, string='Active')

    # Image for frontend display
    image = fields.Binary(
        string='Vehicle Image',
        attachment=True,
        help='Image displayed in search results and detail pages'
    )
    image_url = fields.Char(
        string='Image URL',
        compute='_compute_image_url',
        help='Computed URL for frontend use'
    )

    # Required documents for this vehicle type
    required_document_ids = fields.One2many(
        'logspace.vehicle.type.document',
        'vehicle_type_id',
        string='Required Documents'
    )

    _code_unique = models.Constraint('unique(code)', 'Vehicle type code must be unique!')

    @api.depends('image', 'category_id')
    def _compute_image_url(self):
        """Compute image URL for frontend use"""
        for vt in self:
            if vt.image:
                vt.image_url = f'/web/image/logspace.vehicle.type/{vt.id}/image'
            else:
                # Default images based on category or code
                default_images = {
                    'flatbed': '/appness_logspace/static/src/img/truck_flatbed.jpg',
                    'box': '/appness_logspace/static/src/img/truck_box.jpg',
                    'covered': '/appness_logspace/static/src/img/truck_box.jpg',
                    'mini': '/appness_logspace/static/src/img/truck_mini.jpg',
                    'pickup': '/appness_logspace/static/src/img/truck_pickup.jpg',
                    'heavy': '/appness_logspace/static/src/img/truck_heavy.jpg',
                    'refrigerated': '/appness_logspace/static/src/img/truck_reefer.jpg',
                    'reefer': '/appness_logspace/static/src/img/truck_reefer.jpg',
                    'van': '/appness_logspace/static/src/img/truck_mini.jpg',
                }

                # Try to match by code
                code_lower = (vt.code or '').lower()
                for key, img in default_images.items():
                    if key in code_lower:
                        vt.image_url = img
                        break
                else:
                    # Category-based fallback, keyed on the category CODE (the m2o
                    # recordset itself is unhashable, so it cannot be a dict key).
                    category_images = {
                        'light': '/appness_logspace/static/src/img/truck_mini.jpg',
                        'medium': '/appness_logspace/static/src/img/truck_flatbed.jpg',
                        'heavy': '/appness_logspace/static/src/img/truck_heavy.jpg',
                        'special': '/appness_logspace/static/src/img/truck_reefer.jpg',
                    }
                    vt.image_url = category_images.get(vt.category_id.code,
                        '/appness_logspace/static/src/img/truck_flatbed.jpg')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code'):
                vals['code'] = vals['code'].lower().replace(' ', '_')
        return super(LogspaceVehicleType, self).create(vals_list)
