from odoo import _, api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    attachment_size_limit = fields.Integer(default=2, config_parameter='appness_logspace_portal.attachment_size_limit')