from odoo import models,fields,api,_
from odoo.exceptions import ValidationError,UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    is_swms = fields.Boolean()
    payment_state_auto_sponsership_bill_status = fields.Boolean(compute="_payment_state_auto_sponsership_bill_status",store=True)
    is_sponsership = fields.Boolean(compute="_is_sponsership", store=True)
    
    sponsership_id = fields.Many2one("sale.order")
    sponsership_bill_id = fields.Many2one("account.move")
    sponsership_invoice_id = fields.Many2one("account.move")
    card_spending_id = fields.Many2one("swms.card.spending",copy=False)

    #sponsership
    sponsership_request_id = fields.Many2one("helpdesk.ticket",string="Sponsership Request",related="sponsership_id.request_id")
    sponsership_request_analytic_account_id = fields.Many2one("account.analytic.account",related="sponsership_request_id.analytic_account_id")
    sponsership_family = fields.Many2one("res.partner",string="Sponsership Family",related="sponsership_id.family")
    sponsership_family_member = fields.Many2one("res.partner", related="sponsership_id.family_member")
    show_member = fields.Boolean(compute="_show_member",store=True)
    card_id = fields.Many2one("swms.card",related="sponsership_id.card_id",store=True)

    #Bill from request
    request_id = fields.Many2one("helpdesk.ticket")
    request_analytic_account_id = fields.Many2one("account.analytic.account",related="request_id.analytic_account_id")
    family = fields.Many2one("res.partner",domain="[('is_family','=',True),('is_company','=',True)]")

    is_donation = fields.Boolean()
    payment_journal = fields.Many2one("account.journal",string="Payment Journal")

    @api.depends("invoice_line_ids.product_id.document_types")
    def _show_member(self):
        for rec in self:
            show_member = False
            for line in rec.invoice_line_ids:
                if line.product_id:
                    for type in line.product_id.document_types:
                        if type.is_orphan or type.is_education:
                            show_member = True
            rec.show_member = show_member

    @api.depends('invoice_line_ids.sale_line_ids.order_id')
    def _is_sponsership(self):
        for rec in self:
            order_id = False
            for iline in rec.invoice_line_ids:
                for sline in iline.sale_line_ids:
                    if sline.order_id:
                        if sline.order_id.is_swms and sline.order_id.is_subscription:
                            order_id = sline.order_id
            
            if order_id:
                order = self.env["sale.order"].search([('id','=',order_id.id)],limit=1)
                
                if order.is_swms and order.is_subscription:
                    rec.is_sponsership = True
                    rec.is_swms = True
                    rec.sponsership_id = order_id.id

    @api.depends('payment_state')
    def _payment_state_auto_sponsership_bill_status(self):
        for rec in self:
            if rec.payment_state == 'paid':
                if rec.is_sponsership:
                    if not rec.sponsership_bill_id:
                            self.action_bill_sponsership()
                            rec.payment_state_auto_sponsership_bill_status = True
                    else:
                        rec.payment_state_auto_sponsership_bill_status = False
                else:
                    rec.payment_state_auto_sponsership_bill_status = False
            elif rec.state == 'draft' or rec.payment_state != 'paid':
                rec.payment_state_auto_sponsership_bill_status = False

    # Alrahma Bill to Family
    def action_bill_sponsership(self):
        for rec in self:
            if rec.is_sponsership:
                if not rec.sponsership_bill_id:
                    partner_id = False
                    if rec.sponsership_id.show_member:
                        if rec.sponsership_id.family_member:
                            partner_id = rec.sponsership_id.family_member.id
                    else:
                        if rec.sponsership_id.family:
                            partner_id = rec.sponsership_id.family.id

                    invoice_lines = []
                    for line in rec.invoice_line_ids:
                        record = {
                                'product_id': line.product_id.id,
                                'name': line.name,
                                'quantity': line.quantity,
                                'price_unit': line.price_unit,
                                'tax_ids': line.tax_ids.ids
                            }
                        invoice_lines.append((0, 0, record))

                    data = {
                        'is_swms':True,
                        'sponsership_id': rec.sponsership_id.id,
                        'sponsership_invoice_id':rec.id,
                        'partner_id': partner_id,
                        'move_type': 'in_invoice',
                        'invoice_date': rec.invoice_date,
                        'invoice_line_ids': invoice_lines,
                    }
                    invoice_id = self.env['account.move'].sudo().create(data)
                    rec.sponsership_bill_id = invoice_id.id

    def action_instant_pay(self):
        for invoice in self:
            if invoice.state != 'posted':
                invoice.action_post()
            
            if invoice.payment_state == 'paid':
                raise UserError("Invoice is already paid.")

            if not invoice.payment_journal:
                raise UserError("No bank journal found.")

            # Create payment
            payment = self.env['account.payment'].create({
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': invoice.partner_id.id,
                'amount': invoice.amount_residual,
                'date': fields.Date.today(),
                'journal_id': invoice.payment_journal.id,
                'payment_method_line_id': invoice.payment_journal.inbound_payment_method_line_ids[:1].id,
                'memo': invoice.name,
                # 'move_id': invoice.id,
            })

            payment.action_post()  # Post the payment

    def action_post(self):
        """
        Override to add hard block when customer exceeds credit limit.
        This extends Odoo's built-in credit limit warning to actually block confirmation.
        """
        for rec in self:
            if not rec.card_spending_id and rec.sponsership_id:
                if rec.move_type == 'in_invoice':
                    card_spending_id = self.env["swms.card.spending"].create({
                        "name": "Card has been debited",
                        "account_move_id": rec.id,
                    })
                    rec.card_spending_id = card_spending_id.id
                elif rec.move_type == 'in_refund':
                    card_spending_id = self.env["swms.card.spending"].create({
                        "name": "Card has been credited",
                        "account_move_id": rec.id,
                    })
                    rec.card_spending_id = card_spending_id.id
        
        return super(AccountMove, self).action_post()            