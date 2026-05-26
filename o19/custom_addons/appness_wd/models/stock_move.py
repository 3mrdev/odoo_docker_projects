from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    barcode = fields.Char(string="Barcode",related="product_id.barcode")