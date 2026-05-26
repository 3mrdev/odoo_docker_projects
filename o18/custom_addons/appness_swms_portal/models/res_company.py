from odoo import models,fields,api,_

class ResCompany(models.Model):
    _inherit = 'res.company'

    use_otp_login = fields.Boolean(string="Use Otp Login")
    otp_message = fields.Text(string="Otp Message",help='Make sure to put "%s" in the text so we can replace it with the OTP')
    otp_message_url = fields.Text(string="OTP Url")
    phone_key = fields.Char(string="Phone Key Value")
    message_key = fields.Char(string="Message Key Value")