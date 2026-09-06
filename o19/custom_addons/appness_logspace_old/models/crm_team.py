from odoo import models,fields,api,_

class CrmTeam(models.Model):
    _inherit = "crm.team"

    is_logspace = fields.Boolean(default=False,string="Is Logspace")