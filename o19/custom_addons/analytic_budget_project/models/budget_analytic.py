from odoo import fields, models


class BudgetAnalytic(models.Model):
    _inherit = 'budget.analytic'

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        tracking=True,
    )
    project_account_id = fields.Many2one(
        'account.analytic.account',
        related='project_id.account_id',
        string='Project Analytic Account',
    )
