from odoo import models,fields,api

class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        fields = super(StockRule, self)._get_custom_move_fields()
        fields += ['volume_length','volume_width','volume_height','created_production_id']
        return fields