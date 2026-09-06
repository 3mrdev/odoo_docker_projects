from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    journal_source = fields.Many2one('account.journal', string='Source Journal')
    journal_destination = fields.Many2one('account.journal', string='Destination Journal')

    # Payment method fields
    payment_method_line_source_id = fields.Many2one(
        'account.payment.method.line',
        string='Source Payment Method',
        domain="[('journal_id', '=', journal_source), ('payment_type', '=', 'outbound')]",
        check_company=True,
    )
    payment_method_line_destination_id = fields.Many2one(
        'account.payment.method.line',
        string='Destination Payment Method',
        domain="[('journal_id', '=', journal_destination), ('payment_type', '=', 'inbound')]",
        check_company=True,
    )

    # Warning fields for payment method configuration
    source_payment_method_warning = fields.Boolean(
        compute='_compute_payment_warnings',
        string='Source Payment Method Warning'
    )
    destination_payment_method_warning = fields.Boolean(
        compute='_compute_payment_warnings',
        string='Destination Payment Method Warning'
    )

    # Force journal entries if payment methods lack outstanding accounts
    force_journal_entries = fields.Boolean(
        string='Force Journal Entries',
        help='Check this if payment methods do not have outstanding accounts configured. '
             'The system will use the journal default accounts to create journal entries.'
    )

    @api.depends('journal_source', 'journal_destination', 'payment_method_line_source_id', 'payment_method_line_destination_id')
    def _compute_payment_warnings(self):
        """Compute warning flags when payment methods lack outstanding accounts."""
        for record in self:
            if record.approval_type != 'liquidity_transfer':
                record.source_payment_method_warning = False
                record.destination_payment_method_warning = False
                continue

            # Source payment method warning
            if record.payment_method_line_source_id:
                record.source_payment_method_warning = not bool(
                    record.payment_method_line_source_id.payment_account_id
                )
            elif record.journal_source:
                default_method = self.env['account.payment.method.line'].search([
                    ('journal_id', '=', record.journal_source.id),
                    ('payment_type', '=', 'outbound'),
                ], limit=1)
                record.source_payment_method_warning = default_method and not bool(
                    default_method.payment_account_id
                )
            else:
                record.source_payment_method_warning = False

            # Destination payment method warning
            if record.payment_method_line_destination_id:
                record.destination_payment_method_warning = not bool(
                    record.payment_method_line_destination_id.payment_account_id
                )
            elif record.journal_destination:
                default_method = self.env['account.payment.method.line'].search([
                    ('journal_id', '=', record.journal_destination.id),
                    ('payment_type', '=', 'inbound'),
                ], limit=1)
                record.destination_payment_method_warning = default_method and not bool(
                    default_method.payment_account_id
                )
            else:
                record.destination_payment_method_warning = False

    @api.onchange('journal_source')
    def _onchange_journal_source(self):
        """Set default payment method when journal changes."""
        if self.journal_source and self.approval_type == 'liquidity_transfer':
            method_line = self.env['account.payment.method.line'].search([
                ('journal_id', '=', self.journal_source.id),
                ('payment_type', '=', 'outbound'),
            ], limit=1)
            self.payment_method_line_source_id = method_line

    @api.onchange('journal_destination')
    def _onchange_journal_destination(self):
        """Set default payment method when journal changes."""
        if self.journal_destination and self.approval_type == 'liquidity_transfer':
            method_line = self.env['account.payment.method.line'].search([
                ('journal_id', '=', self.journal_destination.id),
                ('payment_type', '=', 'inbound'),
            ], limit=1)
            self.payment_method_line_destination_id = method_line

    def action_approve(self, approver=None):
        if self.approval_type == 'liquidity_transfer':
            if not self.journal_source or not self.journal_destination:
                raise UserError(_("You must select a source and a destination journal for the liquidity transfer."))
        return super().action_approve(approver)

    def action_create_custom_by_type(self):
        if self.approval_type == 'liquidity_transfer':
            return self._action_create_payments_liquidity_transfer()
        return super().action_create_custom_by_type()

    def _get_outstanding_account_for_payment(self, payment_method_line, journal):
        """
        Determine outstanding account for payment creation.

        Returns:
            - account.account record: Force this account as outstanding_account_id
            - None: Let Odoo compute naturally (standard behavior)

        Logic:
            - If payment method has account: return None (use standard)
            - If no account and force_journal_entries=True: return journal default
            - If no account and force_journal_entries=False: return None
        """
        self.ensure_one()
        if payment_method_line and payment_method_line.payment_account_id:
            # Payment method has outstanding account - use standard behavior
            return None
        elif self.force_journal_entries:
            # No outstanding account but user wants to force - use journal default
            return journal.default_account_id
        else:
            # No outstanding account, no force - let Odoo handle (may not create move)
            return None

    def _action_create_payments_liquidity_transfer(self):
        """Create Payments for Liquidity Transfer.

        Creates two payments:
        1. Outbound payment from source journal
        2. Inbound payment to destination journal

        Uses selected payment methods or defaults. Respects force_journal_entries
        flag to handle missing outstanding accounts.

        This approach ensures:
        - Journal dashboard counts the transactions
        - Payment receipts can be printed
        - Proper integration with bank reconciliation
        - User control over outstanding account handling
        """
        self.ensure_one()

        if not self.journal_source or not self.journal_destination:
            raise UserError(_("You must select a source and a destination journal for the liquidity transfer."))

        liquidity_transfer_account = self.env.company.transfer_account_id
        if not liquidity_transfer_account:
            raise UserError(_("No transfer account configured in company settings."))

        # Build memo text (reference + payment note if provided)
        memo_parts = [self.name]
        if self.payment_note:
            memo_parts.append(self.payment_note)
        memo = ' - '.join(memo_parts)

        # Determine payment method lines (use selected or default)
        payment_method_source = self.payment_method_line_source_id or self.env['account.payment.method.line'].search([
            ('journal_id', '=', self.journal_source.id),
            ('payment_type', '=', 'outbound'),
        ], limit=1)

        payment_method_destination = self.payment_method_line_destination_id or self.env['account.payment.method.line'].search([
            ('journal_id', '=', self.journal_destination.id),
            ('payment_type', '=', 'inbound'),
        ], limit=1)

        # Get outstanding accounts based on warnings and force flag
        outstanding_account_source = self._get_outstanding_account_for_payment(
            payment_method_source, self.journal_source
        )
        outstanding_account_destination = self._get_outstanding_account_for_payment(
            payment_method_destination, self.journal_destination
        )

        # Create source payment (outbound from source journal)
        payment_source = self.env['account.payment'].create({
            'approval_request_id': self.id,
            'payment_type': 'outbound',
            'journal_id': self.journal_source.id,
            'payment_method_line_id': payment_method_source.id if payment_method_source else False,
            'amount': self.amount,
            'date': fields.Date.today(),
            'memo': memo,
            'destination_account_id': liquidity_transfer_account.id,
        })

        # Force outstanding account and generate journal entry if needed
        # (outstanding_account_id is computed/stored, must be set after create)
        if outstanding_account_source:
            payment_source.outstanding_account_id = outstanding_account_source.id
            # Explicitly generate journal entry since write() won't catch computed field change
            payment_source._generate_journal_entry()
            payment_source.move_id.approval_request_id = self.id
            payment_source.move_id.action_post()
            payment_source.state = 'paid' if outstanding_account_source.account_type == 'asset_cash' else 'in_process'

        # Create destination payment (inbound to destination journal)
        payment_destination = self.env['account.payment'].create({
            'approval_request_id': self.id,
            'payment_type': 'inbound',
            'journal_id': self.journal_destination.id,
            'payment_method_line_id': payment_method_destination.id if payment_method_destination else False,
            'amount': self.amount,
            'date': self.date,
            'memo': memo,
            'destination_account_id': liquidity_transfer_account.id,
        })

        # Force outstanding account and generate journal entry if needed
        if outstanding_account_destination:
            payment_destination.outstanding_account_id = outstanding_account_destination.id
            # Explicitly generate journal entry since write() won't catch computed field change
            payment_destination._generate_journal_entry()
            payment_destination.move_id.approval_request_id = self.id
            payment_destination.move_id.action_post()
            payment_destination.state = 'paid' if outstanding_account_destination.account_type == 'asset_cash' else 'in_process'

        # For payments where we didn't force outstanding account, use standard action_post
        payments_to_post = (payment_source if not outstanding_account_source else payment_source.browse([])) + \
                          (payment_destination if not outstanding_account_destination else payment_destination.browse([]))
        if payments_to_post:
            payments_to_post.action_post()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Payments'),
            'res_model': 'account.payment',
            'domain': [('id', 'in', (payments_to_post + payment_source + payment_destination).ids)],
            'view_mode': 'list,form',
            'target': 'current',
        }
