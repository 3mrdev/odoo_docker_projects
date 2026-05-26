from odoo import models, fields, api, _


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    @api.onchange('approval_type')
    def _onchange_approval_type(self):
        # To be extended by child modules for type-specific defaults
        pass
