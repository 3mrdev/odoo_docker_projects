from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    salary_adjustment_ids = fields.One2many('hr.salary.attachment', 'approval_request_id', string='Salary Adjustments')
    salary_adjustment_count = fields.Integer(compute='_compute_salary_adjustment_count')

    loan_debit_account = fields.Many2one('account.account', string='Debit Account')
    loan_journal = fields.Many2one('account.journal', string='Journal')
    loan_salary_adjustment_type = fields.Many2one('hr.payslip.input.type', string='Salary Adjustment Type')
    loan_no_months = fields.Integer(string='Number of Months')
    monthly_amount = fields.Integer(string='Monthly Amount', compute='_compute_monthly_amount')

    employee_id = fields.Many2one("hr.employee", string="Employee", default=lambda self: self.env.user.employee_id)

    @api.onchange('approval_type')
    def _onchange_approval_type(self):
        super()._onchange_approval_type()
        if self.approval_type == 'loan' and self.category_id:
            self.loan_debit_account = self.category_id.default_loan_debit_account
            self.loan_journal = self.category_id.default_loan_journal
            self.loan_salary_adjustment_type = self.category_id.default_salary_adjustment_type

    @api.depends('salary_adjustment_ids')
    def _compute_salary_adjustment_count(self):
        for request in self:
            request.salary_adjustment_count = len(request.salary_adjustment_ids)

    @api.depends('amount', 'loan_no_months')
    def _compute_monthly_amount(self):
        for request in self:
            if request.loan_no_months > 0:
                request.monthly_amount = int(request.amount / request.loan_no_months)
            else:
                request.monthly_amount = 0

    def action_approve(self, approver=None):
        if self.approval_type == 'loan':
            if not self.loan_debit_account or not self.loan_journal or not self.loan_salary_adjustment_type:
                raise UserError(_("You must select a debit account and a journal and a salary adjustment type for the loan."))
            if self.loan_no_months <= 0:
                raise UserError(_("You must select a number of months greater than 0 for the loan."))
        return super().action_approve(approver)

    def action_create_custom_by_type(self):
        if self.approval_type == 'loan':
            return self._action_create_journal_entries_loan()
        return super().action_create_custom_by_type()

    def _action_create_journal_entries_loan(self):
        """Create Journal Entries and Salary Adjustment for Loan."""
        self.ensure_one()

        if not self.loan_debit_account or not self.loan_journal or not self.loan_salary_adjustment_type:
            raise UserError(_("You must select a debit account and a journal and a salary adjustment type for the loan."))

        if self.loan_no_months <= 0:
            raise UserError(_("You must select a number of months greater than 0 for the loan."))

        label = _('Loan %s') % self.name

        journal_entry = self.env['account.move'].create({
            'approval_request_id': self.id,
            'journal_id': self.loan_journal.id,
            'ref': label,
            'date': self.date,
            'line_ids': [
                (0, 0, {
                    'account_id': self.loan_debit_account.id,
                    'name': label,
                    'debit': self.amount,
                }),
                (0, 0, {
                    'account_id': self.loan_journal.default_account_id.id,
                    'name': label,
                    'credit': self.amount,
                }),
            ],
        })
        journal_entry.action_post()

        if self.employee_id:
            self.env['hr.salary.attachment'].create({
                'employee_ids': [(6, 0, [self.employee_id.id])],
                'other_input_type_id': self.loan_salary_adjustment_type.id,
                'date_start': self.date,
                'description': label,
                'total_amount': self.amount,
                'monthly_amount': int(self.amount / self.loan_no_months) if self.loan_no_months > 1 else self.amount,
                'duration_type': 'limited',
                'is_refund': False,
                'approval_request_id': self.id,
            })
        else:
            raise UserError(_("You must select an employee for the loan."))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entries'),
            'res_model': 'account.move',
            'domain': [('id', 'in', [journal_entry.id])],
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_open_salary_adjustments(self):
        """Return the list of salary adjustments the approval request created."""
        self.ensure_one()
        return {
            'name': _('Salary Adjustments'),
            'view_mode': 'list,form',
            'res_model': 'hr.salary.attachment',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.salary_adjustment_ids.ids)],
        }
