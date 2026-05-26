from odoo import models,fields,api,_

class PaymentMethod(models.Model):
    _name = "swms.payment.method"
    _description = "Payment Method"

    name = fields.Char(required=True)
