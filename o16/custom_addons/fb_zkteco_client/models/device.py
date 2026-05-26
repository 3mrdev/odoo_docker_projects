from odoo import fields,models

class Device(models.Model):
    _name = "fb.zkteco.device"

    name = fields.Char(string="Serial Number")
    api_key = fields.Char()
    online = fields.Datetime(string="Online at")
    allow = fields.Boolean()