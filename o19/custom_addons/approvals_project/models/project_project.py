from odoo import fields, models

class ProjectProject(models.Model):
    _inherit = 'project.project'

    def action_open_project_approvals(self):
        self.ensure_one()
        # from_embedded_action = self.env.context.get('from_embedded_action', False)
        return {
            'name': 'Approvals',
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }