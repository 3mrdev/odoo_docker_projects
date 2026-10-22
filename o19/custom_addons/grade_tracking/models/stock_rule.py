from odoo import fields, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_custom_move_fields(self):
        fields = super()._get_custom_move_fields()
        fields += ["mining_location_id", "mining_level_id", "average_grade"]
        return fields
