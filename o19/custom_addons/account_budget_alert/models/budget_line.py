from odoo import models,fields,api

class BudgetLine(models.Model):
    _name = "budget.line"
    _inherit = ["budget.line","mail.thread","mail.activity.mixin"]
    
    budget_alert_type = fields.Selection([
        ("none","None"),
        ("warning","Warning"),
        ("block","Block"),
    ],string="Budget Alert Type",default="none",tracking=True)