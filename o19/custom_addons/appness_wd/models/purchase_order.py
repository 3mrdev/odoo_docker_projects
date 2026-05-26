from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    total_discount = fields.Float(string='Total Discount', compute='_compute_total_discount',store=True)
    amount_before_discount = fields.Float(string='Amount Before Discount', compute='_compute_total_discount',store=True)
    tags_ids = fields.Many2many('purchase.tag', string='Tags')

    @api.depends('order_line.discount_amount','amount_untaxed')
    def _compute_total_discount(self):
        for order in self:
            total_discount_amount = sum(order.order_line.mapped('discount_amount'))
            order.total_discount = total_discount_amount
            
            total = 0
            for line in order.order_line:
                total += line.price_unit * line.product_qty
            order.amount_before_discount = total