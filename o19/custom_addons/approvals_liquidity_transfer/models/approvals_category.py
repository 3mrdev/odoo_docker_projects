from odoo import models, fields, api, _


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    approval_type = fields.Selection(selection_add=[('liquidity_transfer', 'Liquidity Transfer')])

    @api.onchange('approval_type')
    def _onchange_approval_type(self):
        super()._onchange_approval_type()
        if self.approval_type == 'liquidity_transfer':
            self.has_amount = 'required'
            self.has_date = 'required'
