from odoo import models,fields,api

class StockQuant(models.Model):
    _inherit = "stock.quant"

    volume_display = fields.Char(
        string='Line/Square/Cubic',
        related='lot_id.volume_display',
        store=True,
    )
    volume = fields.Float(
        string='Volume',
        related='lot_id.volume',
        store=True,
    )
    volume_total = fields.Float(
        string='Total Volume',
        related='lot_id.volume_total',
        store=True,
    )
        