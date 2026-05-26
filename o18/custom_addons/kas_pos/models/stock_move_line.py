from odoo import models, fields, api

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    quantity = fields.Float('Quantity', digits='BOM Product Unit of Measure', copy=False, store=True,compute='_compute_quantity', readonly=False)