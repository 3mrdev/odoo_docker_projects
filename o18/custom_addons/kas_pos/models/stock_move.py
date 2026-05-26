from odoo import fields,models,api

class StockMove(models.Model):
    _inherit = "stock.move"

    product_uom_qty = fields.Float(
        'Demand',
        digits='BOM Product Unit of Measure',
        default=0, required=True,
        help="This is the quantity of product that is planned to be moved."
             "Lowering this quantity does not generate a backorder."
             "Changing this quantity on assigned moves affects "
             "the product reservation, and should be done with care.")

    quantity = fields.Float('Quantity', compute='_compute_quantity', digits='BOM Product Unit of Measure', inverse='_set_quantity', store=True)