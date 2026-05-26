# -*- coding: utf-8 -*-

from odoo import models, fields, api


class WDCustomerCreditLevel(models.Model):
    _name = 'wd.customer.credit.level'
    _description = 'Customer Credit Level'
    _order = 'sequence, id'

    name = fields.Char(
        string='Level Name',
        required=True,
        help="Name of the credit level (e.g., Bronze, Silver, Gold)"
    )
    credit_limit = fields.Float(
        string='Credit Limit',
        required=True,
        help="Maximum credit limit amount for this level"
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Used for ordering levels"
    )
    limit_type = fields.Selection(
        selection=[
            ('total_exposure', 'Total Exposure (All Debt)'),
            ('overdue_only', 'Overdue Debt Only'),
        ],
        string='Limit Type',
        default='overdue_only',
        required=True,
        help="Choose how the credit limit is applied:\n"
             "- Total Exposure: Blocks if (Total Receivable + Pending Orders + New Invoice) > Limit.\n"
             "- Overdue Only: Blocks if (Overdue Debt > Limit), ignoring future due invoices."
    )
    allowed_delay_days = fields.Integer(
        string='Grace Period (Days)',
        default=0,
        help="Tolerance for overdue invoices. Invoices are not considered 'Overdue' "
             "for credit limit logic until they are past their due date by this many days."
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Set to False to archive this level"
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        help="Company this level belongs to (leave empty for all companies)"
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
        help="Currency used for the credit limit amount"
    )
    partner_count = fields.Integer(
        string='Partners',
        compute='_compute_partner_count',
        help="Number of partners assigned to this level"
    )

    @api.depends()
    def _compute_partner_count(self):
        for level in self:
            level.partner_count = self.env['res.partner'].search_count([
                ('credit_level_id', '=', level.id)
            ])

    def action_view_partners(self):
        """Open list of partners using this credit level."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Partners - {self.name}',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'domain': [('credit_level_id', '=', self.id)],
            'context': {'default_credit_level_id': self.id},
        }
