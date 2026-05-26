from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')