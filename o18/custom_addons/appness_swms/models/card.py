from odoo import models,fields,api

class Card(models.Model):
    _name = 'swms.card'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = 'Card'
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Card Number must be unique!')
    ]

    name = fields.Char(string="Card Number")
    family_id = fields.Many2one("res.partner",domain=[('is_family','=',True),('is_company','=',True)],tracking=True)
    history = fields.One2many("swms.card.spending","card_id") 
    sponserships = fields.One2many("sale.order","card_id")
    history_count = fields.Integer(compute="_calculate_count",store=True)
    sponserships_count = fields.Integer(compute="_calculate_count",store=True)
    card_used = fields.Boolean(compute="_card_used",store=True)
    active = fields.Boolean(default=True)

    @api.depends("history","sponserships")
    def _calculate_count(self):
        for rec in self:
            rec.history_count = len(rec.history)
            rec.sponserships_count = len(rec.sponserships)

    @api.depends("family_id")
    def _card_used(self):
        for rec in self:
            if rec.family_id:
                rec.card_used = True
            else:
                rec.card_used = False

    def action_see_history(self):
        return {
            'name':'Card History',
            'type': 'ir.actions.act_window',
            'res_model': 'swms.card.spending',
            'view_mode': 'list,form',
            'domain': [('card_id', '=', self.id)],
            'context': {'default_card_id': self.id,'create': False},
        }

    def action_see_sponserships(self):
        return {
            'name':'Card Sponserships',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('card_id', '=', self.id)],
            'context': {'default_card_id': self.id,'create': False},
        }

    def unlink(self):
        for rec in self:
            if rec.history:
                raise UserError(_("You cannot delete a card that has history"))
        return super(Card, self).unlink()
    
class FamilyCardSpending(models.Model):
    _name = "swms.card.spending"
    _description = "Card Spending"

    name = fields.Char(required=True)
    account_move_id = fields.Many2one("account.move",required=True)
    account_move_type = fields.Selection(related="account_move_id.move_type",store=True)
    card_id = fields.Many2one("swms.card",related="account_move_id.sponsership_id.card_id",store=True)
    family_id = fields.Many2one("res.partner",related="account_move_id.sponsership_id.family",store=True)
    request_id = fields.Many2one("helpdesk.ticket",related="account_move_id.sponsership_id.request_id",store=True)
    amount = fields.Monetary(compute="_compute_amount",store=True)
    currency_id = fields.Many2one('res.currency',related="account_move_id.currency_id",store=True)
    date = fields.Date(related="account_move_id.date",store=True)
    
    @api.depends("account_move_id")
    def _compute_amount(self):
        for rec in self:
            if rec.account_move_type == "in_invoice":
                rec.amount = rec.account_move_id.amount_total
            elif rec.account_move_type == "in_refund":
                total_used = rec.account_move_id.amount_total - rec.account_move_id.reversed_entry_id.amount_total
                rec.amount = total_used
            else:
                rec.amount = 0
    