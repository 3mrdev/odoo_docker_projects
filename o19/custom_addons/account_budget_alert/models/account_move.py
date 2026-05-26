from odoo import models,fields,api,_
from odoo.exceptions import UserError
from odoo.tools import formatLang
from . import utility

class AccountMove(models.Model):
    _inherit = "account.move"
    
    is_above_budget_alert = fields.Boolean('Is Above Budget Alert', compute='_compute_above_budget_alert',store=True)
    is_above_financial_budget_alert = fields.Boolean('Is Above Financial Budget Alert', compute='_compute_above_budget_alert',store=True)
    
    @api.depends('invoice_line_ids.price_unit', 'invoice_line_ids.quantity', 'state')
    def _compute_above_budget_alert(self):
        for move in self:
            if move.move_type in ["in_invoice"]:
                block_budget,is_above_budget, analytic_account_display = utility.get_budget_alert(self,move,state_field_name='state',date_field_name='invoice_date',product_qty_field_name='quantity',line_field_name='invoice_line_ids',states=['draft','sent'])
                block_financial_budget,is_above_financial_budget, account_display = utility.get_financial_budget_alert(self,move,state_field_name='state',date_field_name='invoice_date',product_qty_field_name='quantity',line_field_name='invoice_line_ids',states=['draft','sent'])
                move.is_above_budget_alert = is_above_budget
                move.is_above_financial_budget_alert = is_above_financial_budget

    def action_budget_alert(self,force_show=True):
        for move in self:
            if move.move_type in ["in_invoice"]:
                block_budget,is_above_budget, analytic_account_display = utility.get_budget_alert(self,move,state_field_name='state',date_field_name='invoice_date',product_qty_field_name='quantity',line_field_name='invoice_line_ids',states=['draft','sent'])
                block_financial_budget,is_above_financial_budget, account_display = utility.get_financial_budget_alert(self,move,state_field_name='state',date_field_name='invoice_date',product_qty_field_name='quantity',line_field_name='invoice_line_ids',states=['draft','sent'])
                
                message = ""
                if is_above_financial_budget:
                    message += _(
                        "You have exceeded the financial budget.\n\n"
                        "%(account_display)s",
                        account_display=account_display,
                    )
                if is_above_budget:
                    message += _(
                        "You have exceeded the analytic budget.\n\n"
                        "%(analytic_account_display)s",
                        analytic_account_display=analytic_account_display,
                    )            
                
                if (block_financial_budget or block_budget) or force_show:
                    raise UserError(message)
    
    def action_post(self):
        """
        Override to add hard block when employee exceeds budget.
        """
        for move in self:
            if move.move_type in ["in_invoice"]:
                move.action_budget_alert(force_show=False)   
        return super(AccountMove, self).action_post()