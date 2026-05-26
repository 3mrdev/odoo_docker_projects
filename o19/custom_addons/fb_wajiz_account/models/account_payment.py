from odoo import models,fields,api

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.depends('journal_id', 'payment_type', 'payment_method_line_id')
    def _compute_outstanding_account_id(self):
        for pay in self:
            if pay.journal_id.company_id.use_outstanding_accounts:
                super()._compute_outstanding_account_id()
            else:
                pay.outstanding_account_id = pay.journal_id.default_account_id