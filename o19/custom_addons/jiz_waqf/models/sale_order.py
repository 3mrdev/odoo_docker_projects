# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    waqf_unit_id = fields.Many2one('jiz.waqf.unit', string='Waqf Unit', tracking=True)
    waqf_id = fields.Many2one('jiz.waqf', string='Waqf', related='waqf_unit_id.waqf_id', store=True)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.waqf_unit_id:
                if order.waqf_unit_id.subscription_ids:
                    other_subscriptions = self.search([
                        ('waqf_unit_id', '=', order.waqf_unit_id.id),
                        ('state', 'in', ['sale', 'done']),
                        ('id', '!=', order.id)
                    ])
                    if other_subscriptions:
                        raise UserError(_("You cannot confirm a subscription for a unit that has another confirmed subscription."))
                
                if order.waqf_unit_id.responsible_id:
                    order.partner_invoice_id = order.waqf_unit_id.responsible_id.id
                    order.partner_shipping_id = order.waqf_unit_id.responsible_id.id
                
                order.waqf_unit_id.status = 'under_rent'
                if order.waqf_unit_id.tenant_id:
                    if order.waqf_unit_id.tenant_id.id == order.partner_id.id:
                        pass
                    else:
                        order.waqf_unit_id.tenant_id = order.partner_id.id
                else:
                    order.waqf_unit_id.tenant_id = order.partner_id.id

                for line in order.order_line:
                    if order.waqf_unit_id.analytic_account_id:
                        line.analytic_distribution = {str(order.waqf_unit_id.analytic_account_id.id): 100}
        return res

    def resume_subscription(self):
        res = super(SaleOrder, self).resume_subscription()
        for order in self:
            if order.waqf_unit_id:
                other_subscriptions = self.search([
                    ('waqf_unit_id', '=', order.waqf_unit_id.id),
                    ('subscription_state', 'in', ['3_progress', '5_renewed','7_upsell']),
                    ('id', '!=', order.id)
                ])
                if other_subscriptions:
                    raise UserError(_("You cannot resume a subscription for a unit that has another running subscription."))
        return res

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for order in self:
            self.set_free_unit(order)
        return res

    def reopen_order(self):
        res = super(SaleOrder, self).reopen_order()
        for order in self:
            if order.waqf_unit_id:
                other_subscriptions = self.search([
                    ('waqf_unit_id', '=', order.waqf_unit_id.id),
                    ('subscription_state', 'in', ['3_progress', '5_renewed','7_upsell']),
                    ('id', '!=', order.id)
                ])
                if other_subscriptions:
                    raise UserError(_("You cannot reopen a subscription for a unit that has another running subscription."))
                else:
                    order.waqf_unit_id.status = 'under_rent'
                    if order.waqf_unit_id.tenant_id:
                        if order.waqf_unit_id.tenant_id.id == order.partner_id.id:
                            pass
                        else:
                            order.waqf_unit_id.tenant_id = order.partner_id.id
                    else:
                        order.waqf_unit_id.tenant_id = order.partner_id.id
        return res

    def set_free_unit(self,order):
        if order.waqf_unit_id:
            other_subscriptions = self.search([
                ('waqf_unit_id', '=', order.waqf_unit_id.id),
                ('subscription_state', 'in', ['3_progress', '5_renewed','7_upsell']),
                ('id', '!=', order.id)
            ])
            if not other_subscriptions:
                order.waqf_unit_id.status = 'free'
                order.waqf_unit_id.tenant_id = False

    @api.constrains('subscription_state')
    def _constrain_subscription_state(self):
        for record in self:
            if record.subscription_state == '6_churn':
                self.set_free_unit(record)