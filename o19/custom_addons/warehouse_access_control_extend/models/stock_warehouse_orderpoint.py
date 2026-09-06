from odoo import fields, models


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    # Boolean flag for record rule bypass pattern
    # When user has no location restrictions (check_location=False),
    # this flag is also False, making the OR condition in record rule evaluate to True
    boolean_orderpoint_flag = fields.Boolean(
        string='Orderpoint Flag', default=False)
