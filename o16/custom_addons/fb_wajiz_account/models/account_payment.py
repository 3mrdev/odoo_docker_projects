from odoo import models,fields,api

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.depends('journal_id', 'payment_type', 'payment_method_line_id')
    def _compute_outstanding_account_id(self):
        for pay in self:
            if pay.payment_type == 'inbound':
                if pay.journal_id.company_id.use_outstanding_accounts:
                    pay.outstanding_account_id = (pay.payment_method_line_id.payment_account_id
                                                or pay.journal_id.company_id.account_journal_payment_debit_account_id)
                else:
                    pay.outstanding_account_id = pay.journal_id.default_account_id
            elif pay.payment_type == 'outbound':
                if pay.journal_id.company_id.use_outstanding_accounts:
                    pay.outstanding_account_id = (pay.payment_method_line_id.payment_account_id
                                                or pay.journal_id.company_id.account_journal_payment_credit_account_id)
                else:
                    pay.outstanding_account_id = pay.journal_id.default_account_id
            else:
                pay.outstanding_account_id = False