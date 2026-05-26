from odoo import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    approval_request_id = fields.Many2one('approval.request', string='Approval Request', index=True)
