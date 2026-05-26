from odoo import models, fields, api


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    quantity = fields.Float('Quantity', readonly=True, digits='BOM Product Unit of Measure')