from odoo import models,fields,api

class BudgetAnalytic(models.Model):
    _inherit = "budget.analytic"
    
    budget_alert_type = fields.Selection([
        ("none","None"),
        ("warning","Warning"),
        ("block","Block"),
    ],string="Budget Alert Type",default="none",help="If you choose:\n-block or warning then it will block or warn for all the budget lines regardless of the value inside the lines\n-none then it will use the condition inside each budget line")