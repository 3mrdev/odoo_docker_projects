from odoo import models,fields,api,_

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    is_above_budget_alert = fields.Boolean('Is Above Budget Alert')
    is_above_financial_budget_alert = fields.Boolean('Is Above Financial Budget Alert')