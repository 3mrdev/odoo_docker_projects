from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    discount_amount = fields.Monetary(compute="tax_discount_amount_compute",store=True)
    tax_amount = fields.Monetary(compute="tax_discount_amount_compute",store=True)
    barcode = fields.Char(string="Barcode",related="product_id.barcode")

    @api.depends("product_uom_qty","price_unit","tax_ids","discount","price_subtotal")
    def tax_discount_amount_compute(self):
        for line in self:
            subtotal = line.product_uom_qty * line.price_unit
            line.discount_amount = subtotal * (line.discount/100)
            total_tax_amount = 0
            for tax in line.tax_ids:
                total_tax_amount += line.price_subtotal * (tax.amount/100) 
            line.tax_amount = total_tax_amount
