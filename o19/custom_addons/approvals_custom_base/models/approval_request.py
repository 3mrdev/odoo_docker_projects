from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    # Journal entries fields
    journal_entries_count = fields.Integer(compute='_compute_journal_entries_count')
    journal_ids = fields.One2many('account.move', 'approval_request_id', string='Journal Entries')

    # Payment fields (used by child modules for payment generation)
    payment_note = fields.Text(string='Payment Notes', help="Notes to include in payment memo/reference")
    payment_ids = fields.One2many('account.payment', 'approval_request_id', string='Payments')
    payments_count = fields.Integer(compute='_compute_payments_count')

    @api.onchange('approval_type')
    def _onchange_approval_type(self):
        """Hook method to be extended by child modules for approval type-specific logic."""
        pass

    def _compute_journal_entries_count(self):
        for request in self:
            request.journal_entries_count = len(request.journal_ids)

    @api.depends('payment_ids')
    def _compute_payments_count(self):
        for request in self:
            request.payments_count = len(request.payment_ids)

    def _get_custom_values(self):
        return {}

    def action_cancel(self):
        """Override to notify Journal Entries when the Approval Request is cancelled."""
        res = super().action_cancel()
        for journal_entry in self.journal_ids:
            journal_entry._activity_schedule_with_view(
                'mail.mail_activity_data_warning',
                views_or_xmlid='approvals_custom_base.exception_approval_request_canceled',
                user_id=self.env.user.id,
                render_context={
                    'approval_requests': self,
                }
            )
        return res

    def action_create_custom_by_type(self):
        """Create custom records based on approval type (journal entries, stock transfers, etc).
        Override this method in child modules to implement type-specific logic."""
        self.ensure_one()
        raise UserError(_("No custom creation logic defined for this approval type."))

    def action_open_journal_entries(self):
        """Return the list of journal entries the approval request created."""
        self.ensure_one()
        return {
            'name': _('Journal Entries'),
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.journal_ids.ids)],
        }

    def action_open_payments(self):
        """Return the list of payments the approval request created."""
        self.ensure_one()
        return {
            'name': _('Payments'),
            'view_mode': 'list,form',
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.payment_ids.ids)],
        }
