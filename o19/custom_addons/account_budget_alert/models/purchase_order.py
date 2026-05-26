from odoo import models,fields,api,_
from odoo.tools import formatLang
from odoo.exceptions import UserError
from . import utility

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    is_above_budget_alert = fields.Boolean('Is Above Budget Alert', compute='_compute_above_budget_alert',store=True)
    is_above_financial_budget_alert = fields.Boolean('Is Above Financial Budget Alert', compute='_compute_above_budget_alert',store=True)
    
    @api.depends('order_line.price_unit', 'order_line.product_qty', 'order_line.qty_invoiced', 'state')
    def _compute_above_budget_alert(self):
        for order in self:
            block_budget,is_above_budget, analytic_account_display = utility.get_budget_alert(self,order,state_field_name='state',date_field_name='date_order',product_qty_field_name='product_qty',line_field_name='order_line',states=['draft','sent','to_approve'])
            financial_block_budget,is_above_financial_budget, account_display = utility.get_financial_budget_alert(self,order,state_field_name='state',date_field_name='date_order',product_qty_field_name='product_qty',line_field_name='order_line',states=['draft','sent','to_approve'])
            order.is_above_budget_alert = is_above_budget
            order.is_above_financial_budget_alert = is_above_financial_budget

    def action_budget_alert(self,force_show=True):
        for order in self:
            block_budget,is_above_budget, analytic_account_display = utility.get_budget_alert(self,order,state_field_name='state',date_field_name='date_order',product_qty_field_name='product_qty',line_field_name='order_line',states=['draft','sent','to_approve'])
            financial_block_budget,is_above_financial_budget, account_display = utility.get_financial_budget_alert(self,order,state_field_name='state',date_field_name='date_order',product_qty_field_name='product_qty',line_field_name='order_line',states=['draft','sent','to_approve'])
            
            message = ""
            if is_above_financial_budget:
                message += _(
                    "Buyer '%(user)s' has exceeded the financial budget.\n\n"
                    "%(account_display)s",
                    user=order.user_id.name,
                    account_display=account_display,
                )
            if is_above_budget:
                message += _(
                    "Buyer '%(user)s' has exceeded the analytic budget.\n\n"
                    "%(analytic_account_display)s",
                    user=order.user_id.name,
                    analytic_account_display=analytic_account_display,
                )
            
            if (block_budget or financial_block_budget) or force_show:
                raise UserError(message)
    
    def button_confirm(self):
        """
        Override to add hard block when buyer exceeds budget.
        """
        self.action_budget_alert(force_show=False)
        return super(PurchaseOrder, self).button_confirm()
