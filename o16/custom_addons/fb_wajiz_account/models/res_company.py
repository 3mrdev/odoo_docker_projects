from odoo import models,fields,api

class ResCompany(models.Model):
    _inherit = 'res.company'

    use_outstanding_accounts = fields.Boolean(string='Use Outstanding Accounts', default=False)
