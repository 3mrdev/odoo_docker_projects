from odoo import models,fields,api

class AccountReportBudgetItem(models.Model):
    _name = "account.report.budget.item"
    _inherit = ["account.report.budget.item","mail.thread","mail.activity.mixin"]
    
    budget_alert_type = fields.Selection([
        ("none","None"),
        ("warning","Warning"),
        ("block","Block"),
    ],string="Budget Alert Type",default="none",tracking=True)