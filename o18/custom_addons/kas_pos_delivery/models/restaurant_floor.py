# -*- coding: utf-8 -*-
from odoo import api, fields, models


class RestaurantFloor(models.Model):
    _inherit = 'restaurant.floor'

    default_customer = fields.Many2one(
        'res.partner',
        string='Default Customer',
        help='Customer that will be automatically assigned to orders when a table on this floor is selected.',
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Extend POS data fields to include default_customer for frontend access."""
        result = super()._load_pos_data_fields(config_id)
        result.append('default_customer')
        return result
