from odoo import _, api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_auth_otp = fields.Boolean("Use OTP Verification", related='company_id.use_otp_login',store=True)
    otp_message = fields.Text(string="Otp Message", related='company_id.otp_message',store=True)
    otp_message_url = fields.Text(string="OTP Url", related='company_id.otp_message_url',store=True)
    phone_key = fields.Char(string="Phone Key Value", related='company_id.phone_key',store=True)
    message_key = fields.Char(string="Message Key Value", related='company_id.message_key', store=True)
    
    attachment_size_limit = fields.Integer(default=2, config_parameter='appness_swms_portal.attachment_size_limit')