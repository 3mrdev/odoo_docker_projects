from odoo import models,fields,api,_
from odoo.exceptions import UserError

class SaleMRPBoMLine(models.Model):
    _name = 'sale.mrp.bom.line'
    _description = 'Sale MRP BoM Line'
    _inherit = ['mail.thread','mail.activity.mixin']

    product_id = fields.Many2one('product.product',string="Product",required=True,tracking=True)
    lot_id = fields.Many2one('stock.lot',string="Lot",required=True,tracking=True)
    product_yield = fields.Float(string="Expected Yield",compute="_cal_product_yeild",store=True)
    quantity = fields.Float(string="Quantity",tracking=True)
    sale_order_line_id = fields.Many2one('sale.order.line',string="Sale Order Line",required=True,tracking=True)
    order_id = fields.Many2one('sale.order',string="Order",related='sale_order_line_id.order_id',store=True)
    order_id_domain = fields.Many2one('sale.order',string="Order")

    @api.depends("sale_order_line_id","lot_id","quantity")
    def _cal_product_yeild(self):
        for rec in self:
            product_yield = 0
            if rec.sale_order_line_id and rec.lot_id:
                if rec.sale_order_line_id.volume > 0:
                    product_yield = (rec.lot_id.volume * rec.quantity)/rec.sale_order_line_id.volume

            rec.product_yield = product_yield

    @api.constrains('lot_id','quantity')
    def _check_lot_id(self):
        for record in self:
            lot_count = 0
            lot_used_quantity = 0
            for line in record.sale_order_line_id.sale_mrp_bom_lines:
                if line.lot_id.id == record.lot_id.id:
                    lot_count += 1
                    lot_used_quantity += line.quantity

            if lot_count > 1:
                raise UserError(_("Lot %s is already used in sale order line %s") % (record.lot_id.display_name, record.sale_order_line_id.display_name))

            if lot_used_quantity > record.lot_id.product_qty:
                raise UserError(_("Lot Quantity used %s is greater than lot quantity %s") % (lot_used_quantity, record.lot_id.product_qty))