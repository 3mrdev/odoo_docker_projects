# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from datetime import date


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    inspection_signiture = fields.Binary(string='Inspection Signiture')
    inspector_id = fields.Many2one('res.users', string='Inspector')
    date_of_inspection = fields.Date(string='Date of Inspection')
    gs1_company_prefix = fields.Char(string='GS1 Company Prefix (GCP)')
    chassis_numbers_count = fields.Integer(string='Chassis Numbers Count', compute='_compute_chassis_numbers_count')
    gln_certs_count = fields.Integer(string='GLN Certs Count', compute='_compute_gln_certs_count')
    last_paid_invoice_date = fields.Date(string='Last Paid Invoice Date',compute='_compute_last_paid_invoice_date',store=True)
    last_paid_invoice_id = fields.Many2one('account.move',string="Last Paid Invoice",compute='_compute_last_paid_invoice_date',store=True)
    show_rop_letter = fields.Boolean(compute='_compute_show_rop_letter',store=True)
    show_gs1_cert = fields.Boolean(compute='_compute_show_gs1_cert',store=True)
    manager_signature = fields.Many2one('res.users', string='Manager Signature')
    payment_voucher_link = fields.Char(string='Payment Voucher Link')

    @api.model
    def default_get(self, fields):
        result = super().default_get(fields)
        if self.env.company.manager_signature:
            result['manager_signature'] = self.env.company.manager_signature.id
        return result

    @api.depends('company_id.show_rop_letter')
    def _compute_show_rop_letter(self):
        for record in self:
            record.show_rop_letter = record.company_id.show_rop_letter
    
    @api.depends('company_id.show_gs1_cert')
    def _compute_show_gs1_cert(self):
        for record in self:
            record.show_gs1_cert = record.company_id.show_gs1_cert
    
    @api.depends('invoice_ids.payment_state')
    def _compute_last_paid_invoice_date(self):
        for record in self:
            if record.invoice_ids:
                if record.invoice_ids.filtered(lambda x: x.state == 'posted' and x.payment_state == 'paid'):
                    last_paid_invoice_id = record.invoice_ids.filtered(lambda x: x.state == 'posted' and x.payment_state == 'paid')[-1]
                    record.last_paid_invoice_date = last_paid_invoice_id.invoice_date
                    record.last_paid_invoice_id = last_paid_invoice_id
                else:
                    record.last_paid_invoice_date = False
                    record.last_paid_invoice_id = False
            else:
                record.last_paid_invoice_date = False
                record.last_paid_invoice_id = False

    @api.depends('order_line.chassis_numbers')
    def _compute_chassis_numbers_count(self):
        for order in self:
            chassis_numbers_count = 0
            for line in order.order_line:
                chassis_numbers_count += len(line.chassis_numbers)
            order.chassis_numbers_count = chassis_numbers_count

    @api.depends('order_line.gln_certs')
    def _compute_gln_certs_count(self):
        for order in self:
            gln_certs_count = 0
            for line in order.order_line:
                gln_certs_count += len(line.gln_certs)
            order.gln_certs_count = gln_certs_count

    def action_view_chassis_numbers(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'obc.chassis',
            'name': 'Chassis Numbers',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id_domain': self.id},
            'view_mode': 'list',
            'target': 'current',
        }

    def action_view_gln_certs(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'gln.cert',
            'name': 'GLN Certs',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id_domain': self.id},
            'view_mode': 'list',
            'target': 'current',
        }