# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    waqf_id = fields.Many2one('jiz.waqf', string='Waqf', compute='_compute_waqf_details', store=True)
    unit_id = fields.Many2one('jiz.waqf.unit', string='Unit', compute='_compute_waqf_details', store=True)
    sell_waqf_id = fields.Many2one('jiz.waqf', string='Sell Waqf')

    @api.depends('invoice_line_ids.sale_line_ids.order_id')
    def _compute_waqf_details(self):
        for move in self:
            waqf_id = False
            unit_id = False
            for line in move.invoice_line_ids:
                if line.sale_line_ids:
                    order = line.sale_line_ids[0].order_id
                    waqf_id = order.waqf_id.id
                    unit_id = order.waqf_unit_id.id
                    break  # Assuming all lines are from the same SO
            move.waqf_id = waqf_id
            move.unit_id = unit_id

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for move in self:
            if move.sell_waqf_id and move.sell_waqf_id.analytic_distribution:
                for line in move.invoice_line_ids:
                    line.analytic_distribution = move.sell_waqf_id.analytic_distribution

        return res
