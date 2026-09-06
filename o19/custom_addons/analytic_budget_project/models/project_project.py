from odoo import models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    def action_open_project_budgets(self):
        self.ensure_one()
        return {
            'name': 'Budgets',
            'type': 'ir.actions.act_window',
            'res_model': 'budget.analytic',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }
