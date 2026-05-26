from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    discount_amount = fields.Monetary(compute="tax_discount_amount_compute",store=True)
    tax_amount = fields.Monetary(compute="tax_discount_amount_compute",store=True)
    barcode = fields.Char(string="Barcode",related="product_id.barcode")
    # sequence = fields.Integer(default=1)
    # sequence = fields.Integer(compute='_compute_sequence', store=True, readonly=False, precompute=True)
    # sequence_number = fields.Integer(string='#',compute='_compute_sequence_number',store=True, help='Line Numbers') #,compute='_compute_sequence_number',store=True,

    # @api.depends('sequence','move_id')
    # def _compute_sequence_number(self):
    #     """Function to compute line numbers"""
    #     for line in self:
    #         sequence_number = 0
    #         for move_line in line.move_id.line_ids:
    #             if move_line.display_type == 'product':
    #                 sequence_number += 1
    #                 move_line.sequence_number = sequence_number

    @api.depends("quantity","price_unit","tax_ids","discount","price_subtotal")
    def tax_discount_amount_compute(self):
        for line in self:
            subtotal = line.quantity * line.price_unit
            line.discount_amount = subtotal * (line.discount/100)
            total_tax_amount = 0
            for tax in line.tax_ids:
                total_tax_amount += line.price_subtotal * (tax.amount/100) 
            line.tax_amount = total_tax_amount
