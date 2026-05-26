from odoo import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'

    allow_refund_button = fields.Boolean("Allow Refund Button", help="Allow to show refund button.")
    allow_cancel_button = fields.Boolean("Allow Cancel Order Button", help="Allow to show cancel order button.")