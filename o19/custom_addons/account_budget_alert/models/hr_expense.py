from odoo import models,fields,api,_
from odoo.tools import formatLang
from odoo.exceptions import UserError
from . import utility

class HRExpense(models.Model):
    _inherit = "hr.expense"

    is_above_budget_alert = fields.Boolean('Is Above Budget Alert', compute='_compute_above_budget_alert',store=True)
    is_above_financial_budget_alert = fields.Boolean('Is Above Financial Budget Alert', compute='_compute_above_budget_alert',store=True)
    
    @api.depends('total_amount_currency','account_id','price_unit', 'quantity', 'state','analytic_distribution')
    def _compute_above_budget_alert(self):
        for record in self:
            block_budget,is_above_budget, analytic_account_display = utility.get_budget_alert(self,record,is_expense=True,state_field_name='state',date_field_name='date',product_qty_field_name='quantity',line_field_name='expense_line_ids',states=['draft'])
            block_financial_budget,is_above_financial_budget, financial_account_display = utility.get_financial_budget_alert(self,record,is_expense=True,state_field_name='state',date_field_name='date',product_qty_field_name='quantity',line_field_name='expense_line_ids',states=['draft'])
            record.is_above_budget_alert = is_above_budget
            record.is_above_financial_budget_alert = is_above_financial_budget

    def action_budget_alert(self,force_show=True):
        for record in self:
            block_budget,is_above_budget, analytic_account_display = utility.get_budget_alert(self,record,is_expense=True,state_field_name='state',date_field_name='date',product_qty_field_name='quantity',line_field_name='expense_line_ids',states=['draft'])
            block_financial_budget,is_above_financial_budget, financial_account_display = utility.get_financial_budget_alert(self,record,is_expense=True,state_field_name='state',date_field_name='date',product_qty_field_name='quantity',line_field_name='expense_line_ids',states=['draft'])

            message = ""
            if is_above_financial_budget:
                message += _(
                    "Employee '%(user)s' has exceeded the financial budget.\n\n"
                    "%(financial_account_display)s",
                    user=record.employee_id.name,
                    financial_account_display=financial_account_display,
                )
            if is_above_budget:
                message += _(
                    "Employee '%(user)s' has exceeded the analytic budget.\n\n"
                    "%(analytic_account_display)s",
                    user=record.employee_id.name,
                    analytic_account_display=analytic_account_display,
                )
            
            if (block_budget or block_financial_budget) or force_show:
                raise UserError(message)
    
    def action_submit(self):
        """
        Override to add hard block when employee exceeds budget.
        """
        self.action_budget_alert(force_show=False)
        return super(HRExpense, self).action_submit()
