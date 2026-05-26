from odoo import fields, models

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    project_id = fields.Many2one('project.project', string='Project')

    def _get_custom_values(self):
        res = super()._get_custom_values()
        if self.project_id:
            res['project_id'] = self.project_id.id
        return res
