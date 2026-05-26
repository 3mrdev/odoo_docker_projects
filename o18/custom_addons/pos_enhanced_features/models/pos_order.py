from odoo import models, fields, api


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    flavor_quantities = fields.Text(
        string="Mix Quantities",
        help="JSON dict mapping PTAV IDs to their selected counts, e.g. {'12': 2, '15': 1}")

    @api.model
    def _load_pos_data_fields(self, config_id):
        result = super()._load_pos_data_fields(config_id)
        result += ['flavor_quantities']
        return result
