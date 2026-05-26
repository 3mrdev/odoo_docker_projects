from odoo import models,fields,api,_

class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_swms = fields.Boolean()
    request_id = fields.Many2one("helpdesk.ticket")