from odoo import models, fields, api, _
from . import utility

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('partner_id')
    def _onchange_partner_id_block(self):
        for move in self:
            # Only check for customer invoices
            if move.move_type == 'out_invoice' and move.partner_id:
                if move.partner_id:
                    utility._block_invoice(self,move)

    def action_post(self):
        """
        Override to add hard block when customer exceeds credit limit.
        This extends Odoo's built-in credit limit warning to actually block confirmation.
        """
        for move in self:
            # Only check for customer invoices
            if move.move_type == 'out_invoice' and move.partner_id:
                utility._block_invoice(self,move)
        
        return super(AccountMove, self).action_post()

    credit_note_ref = fields.Char()
    return_pickings = fields.One2many('stock.picking', 'credit_note_id', string='Return Pickings')
    return_pickings_count = fields.Integer(compute='_compute_return_pickings_count',store=True)
    total_discount = fields.Float(string='Total Discount', compute='_compute_total_discount',store=True)
    amount_before_discount = fields.Float(string='Amount Before Discount', compute='_compute_total_discount',store=True)

    @api.depends('invoice_line_ids.discount_amount','amount_untaxed')
    def _compute_total_discount(self):
        for move in self:
            total_discount_amount = sum(move.invoice_line_ids.mapped('discount_amount'))
            move.total_discount = total_discount_amount
            
            total = 0
            for line in move.invoice_line_ids:
                total += line.price_unit * line.quantity
            move.amount_before_discount = total

    @api.depends('return_pickings')
    def _compute_return_pickings_count(self):
        for move in self:
            move.return_pickings_count = len(move.return_pickings)

    def open_return_products(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'name': 'Returned Products',
            'view_mode': 'list,form',
            'domain': [('credit_note_id', '=', self.id)],
            'target': 'current',
        }

    def action_return_products(self):
        search_exsiting_pickings = self.env['stock.picking'].search([
            ('credit_note_id', '=', self.id)
        ])
        if search_exsiting_pickings:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'name': 'Returned Products',
                'view_mode': 'list,form',
                'domain': [('credit_note_id', '=', self.id)],
                'target': 'current',
            }

        move_ids = []
        for line in self.invoice_line_ids:
            move_ids.append((0,0,{
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
            }))

        picking_type_id = False
        if self.move_type == 'out_refund':
            picking_type_id = self.env.ref('stock.picking_type_in').id
        elif self.move_type == 'in_refund':
            picking_type_id = self.env.ref('stock.picking_type_out').id
        else:
            raise UserError("This invoice is not a credit note")

        picking_id = self.env['stock.picking'].create({
            'partner_id': self.partner_id.id,
            'credit_note_id': self.id,
            'picking_type_id': picking_type_id,
            'move_type':'direct',
            'move_ids':move_ids
        })

        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'stock.picking',
        #     'name': 'Returned Products',
        #     'view_mode': 'form',
        #     'target': 'new',
        #     'res_id': picking_id.id,
        # }

    @api.model
    def _prepare_move_for_asset_depreciation(self, vals):
        asset = vals['asset_id']
        move_vals = super(AccountMove, self)._prepare_move_for_asset_depreciation(vals)
        analytic_distribution_credit = asset.analytic_distribution_credit
        analytic_distribution_debit = asset.analytic_distribution_debit
        if not asset.analytic_both:
            for line in move_vals['line_ids']:
                if line[2]['credit'] > 0:
                    line[2]['analytic_distribution'] = analytic_distribution_credit
                elif line[2]['debit'] > 0:
                    line[2]['analytic_distribution'] = analytic_distribution_debit

        return move_vals