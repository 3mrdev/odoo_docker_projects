from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_allow_refund_button = fields.Boolean(string="Allow Refund Button",related='pos_config_id.allow_refund_button',readonly=False)
    pos_allow_cancel_button = fields.Boolean(string="Allow Cancel Button",related='pos_config_id.allow_cancel_button',readonly=False)