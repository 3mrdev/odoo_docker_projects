from odoo import models, fields, api
from . import utility

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    total_discount = fields.Float(string='Total Discount', compute='_compute_total_discount',store=True)
    # amount_before_discount = fields.Float(string='Amount Before Discount', compute='_compute_total_discount',store=True)

    @api.depends('order_line.discount_amount','amount_untaxed')
    def _compute_total_discount(self):
        for order in self:
            total_discount_amount = sum(order.order_line.mapped('discount_amount'))
            order.total_discount = total_discount_amount
            # total = 0
            # for line in order.order_line:
            #     total += line.price_unit * line.product_uom_qty
            # order.amount_before_discount = total

    @api.onchange('partner_id')
    def _onchange_partner_id_block(self):
        for order in self:
            if order.partner_id:
                utility._block_invoice(self,order)

    def action_confirm(self):
        for order in self:
            utility._block_invoice(self,order)
        return super(SaleOrder, self).action_confirm()