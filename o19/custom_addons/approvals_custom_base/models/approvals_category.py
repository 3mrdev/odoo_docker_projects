from odoo import models, fields, api, _


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    executor_group_ids = fields.Many2many(
        'res.groups',
        string='Action Executor Groups',
        help='Groups whose members can perform post-approval actions '
             'on approved requests of this category.',
    )

    @api.onchange('approval_type')
    def _onchange_approval_type(self):
        # To be extended by child modules for type-specific defaults
        pass
