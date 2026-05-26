from odoo import models,fields,api,_

class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_logspace = fields.Boolean(default=False,string="Is Logspace")