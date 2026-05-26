# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    journal_entries_count = fields.Integer(compute='_compute_journal_entries_count')
    journal_entries = fields.One2many('account.move', 'approval_request_id', string='Journal Entries')

    journal_source = fields.Many2one('account.journal', string='Source Journal')
    journal_destination = fields.Many2one('account.journal', string='Destination Journal')

    @api.depends('journal_entries')
    def _compute_journal_entries_count(self):
        for request in self:
            request.journal_entries_count = len(request.journal_entries)

    def action_approve(self, approver=None):
        if self.approval_type == 'liquidity_transfer' and not self.journal_source or not self.journal_destination:
            raise UserError(_("You must select a source and a destination journal for the liquidity transfer."))
        return super().action_approve(approver)

    def action_cancel(self):
        """ Override to notify Journal Entries when the Approval Request is cancelled. """
        res = super().action_cancel()
        journal_entries = self.journal_entries
        for journal_entry in journal_entries:
            journal_entry._activity_schedule_with_view(
                'mail.mail_activity_data_warning',
                views_or_xmlid='approvals_purchase.exception_approval_request_canceled',
                user_id=self.env.user.id,
                render_context={
                    'approval_requests': self,
                }
            )
        return res

    def action_confirm(self):
        for request in self:
            if request.approval_type == 'liquidity_transfer' and not request.journal_source or not request.journal_destination:
                raise UserError(_("You must select a source and a destination journal for the liquidity transfer."))
        return super().action_confirm()

    def action_create_journal_entries(self):
        """ Create and/or modifier Journal Entries. """
        self.ensure_one()

        liquidity_transfer_account = self.env.company.transfer_account_id
        label = _('Liquidity Transfer %s') % self.name

        journal_entrie_source = self.env['account.move'].create({
            'approval_request_id': self.id,
            'journal_id': self.journal_source.id,
            'ref': label,
            'date': self.date,
            'line_ids': [(0, 0, {
                'account_id': liquidity_transfer_account.id,
                'name': label,
                'debit': self.amount,
            }), (0, 0, {
                'account_id': self.journal_source.default_account_id.id,
                'name': label,
                'credit': self.amount,
            })],
        })
        journal_entrie_source.action_post()

        journal_entrie_destination = self.env['account.move'].create({
            'approval_request_id': self.id,
            'journal_id': self.journal_destination.id,
            'ref': label,
            'date': self.date,
            'line_ids': [(0, 0, {
                'account_id': liquidity_transfer_account.id,
                'name': label,
                'credit': self.amount,
            }), (0, 0, {
                'account_id': self.journal_destination.default_account_id.id,
                'name': label,
                'debit': self.amount,
            })],
        })
        journal_entrie_destination.action_post()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entries'),
            'res_model': 'account.move',
            'domain': [('id', 'in', [journal_entrie_source.id, journal_entrie_destination.id])],
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_open_journal_entries(self):
        """ Return the list of journal entries the approval request created. """
        self.ensure_one()
        action = {
            'name': _('Journal Entries'),
            'view_type': 'list',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.journal_entries.ids)],
        }
        return action
