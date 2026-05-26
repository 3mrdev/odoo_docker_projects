from odoo import models,fields,api,_

class ResPartner(models.Model):
    _inherit = "res.partner"

    is_logspace_customer = fields.Boolean(default=False,string="Is Logspace Customer")
    is_logspace_provider = fields.Boolean(default=False,string="Is Logspace Provider")
    allow_editing_portal = fields.Boolean(default=False,string="Allow Editing Portal")