from odoo import api, fields, models


class BudgetLine(models.Model):
    _inherit = 'budget.line'

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        related='budget_analytic_id.project_id',
        store=True,
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        """Default the analytic account to the project's analytic account
        when creating budget lines from a project context."""
        defaults = super().default_get(fields_list)
        if self.env.context.get('default_project_id'):
            project = self.env['project.project'].browse(
                self.env.context['default_project_id']
            )
            if project.exists() and project.account_id:
                if not defaults.get('account_id'):
                    defaults['account_id'] = project.account_id.id
        return defaults
