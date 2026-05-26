from odoo import models,fields,api,_

class Sequence(models.Model):
    _inherit = "ir.sequence"

    swms_allow = fields.Boolean()