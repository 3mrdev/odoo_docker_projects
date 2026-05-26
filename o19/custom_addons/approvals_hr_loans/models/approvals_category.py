from odoo import models, fields, api, _


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    approval_type = fields.Selection(selection_add=[('loan', 'Loan')])

    default_loan_debit_account = fields.Many2one('account.account', string='Default Loan Debit Account')
    default_loan_journal = fields.Many2one('account.journal', string='Default Loan Journal')
    default_salary_adjustment_type = fields.Many2one('hr.payslip.input.type', string='Default Loan Salary Adjustment Type')

    @api.onchange('approval_type')
    def _onchange_approval_type(self):
        super()._onchange_approval_type()
        if self.approval_type == 'loan':
            self.has_amount = 'required'
            self.has_date = 'required'
            self.automated_sequence = True
            self.sequence_code = 'LO'
