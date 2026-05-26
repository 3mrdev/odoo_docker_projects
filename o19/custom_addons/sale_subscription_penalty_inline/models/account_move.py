# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class AccountMove(models.Model):
    _inherit = 'account.move'

    last_penalty_date = fields.Date(
        string="Last Penalty Date",
        help="Date when the last penalty line was added to this invoice",
        readonly=True,
        copy=False
    )
    
    penalty_line_ids = fields.One2many(
        'account.move.line',
        compute='_compute_penalty_line_ids',
        string="Penalty Lines",
        help="Invoice lines that represent penalty charges"
    )
    
    penalty_count = fields.Integer(
        compute='_compute_penalty_line_ids',
        string="Number of Penalties",
        help="Count of penalty lines added to this invoice"
    )
    
    @api.depends('invoice_line_ids.is_penalty_line')
    def _compute_penalty_line_ids(self):
        for move in self:
            penalty_lines = move.invoice_line_ids.filtered(lambda l: l.is_penalty_line)
            move.penalty_line_ids = penalty_lines
            move.penalty_count = len(penalty_lines)
    
    def _should_add_penalty_line(self):
        """
        Check if this invoice should have a penalty line added.
        
        Returns:
            bool: True if penalty should be added
        """
        self.ensure_one()
        
        # Must be a posted customer invoice
        if self.move_type != 'out_invoice' or self.state != 'posted':
            return False
        
        # Must be unpaid or partially paid
        if self.payment_state not in ['not_paid', 'partial']:
            return False
        
        # Must have deferred dates (subscription invoice)
        # Only get lines that have deferred_end_date (subscription lines)
        lines_with_deferred_dates = self.invoice_line_ids.filtered(lambda l: l.deferred_end_date)
        if not lines_with_deferred_dates:
            return False
        
        deferred_end_date = max(lines_with_deferred_dates.mapped('deferred_end_date'))
        today = fields.Date.today()
        
        # Must be past the deferred end date
        if deferred_end_date >= today:
            return False
        
        # Check yearly recurrence
        if not self.last_penalty_date:
            # No penalty added yet - add first penalty
            return True
        else:
            # Check if 1 year has passed since last penalty
            next_penalty_due = self.last_penalty_date + relativedelta(years=1)
            
            #TODO: Remove if you want to add penalties every year
            # return today >= next_penalty_due
            return False
    
    def _add_penalty_invoice_line(self, penalty_product, penalty_amount):
        """
        Add a penalty line to this invoice.
        
        Args:
            penalty_product: product.product record
            penalty_amount: float
            
        Returns:
            account.move.line: Created penalty line
        """
        self.ensure_one()

        lines_with_deferred_dates = self.invoice_line_ids.filtered(lambda l: l.deferred_end_date)
        if not lines_with_deferred_dates:
            return False
        
        deferred_end_date = max(lines_with_deferred_dates.mapped('deferred_end_date'))
        
        # Calculate penalty number
        penalty_number = self.penalty_count + 1
        penalty_year = deferred_end_date.year + penalty_number - 1
        description = f"Late Payment Penalty #{penalty_number} for being late on year {penalty_year}"

        if penalty_amount > 0 and penalty_amount < 1:
            penalty_amount = penalty_amount * self.amount_untaxed

        # Create the penalty line
        penalty_line = self.env['account.move.line'].create({
            'move_id': self.id,
            'product_id': penalty_product.id,
            'name': description,
            'quantity': 1,
            'price_unit': penalty_amount,
            'tax_ids': [(6, 0, penalty_product.taxes_id.ids)],
            'is_penalty_line': True,
        })
        
        # Update last penalty date
        self.last_penalty_date = deferred_end_date.replace(year=penalty_year)
        
        # Post a message
        self.message_post(
            body=f"Penalty charge #{penalty_number} ({penalty_amount}) added for late payment.",
            subject=f"Late Payment Penalty #{penalty_number}"
        )
        
        return penalty_line
    
    def action_view_penalty_lines(self):
        """Smart button action to view penalty lines"""
        self.ensure_one()
        return {
            'name': 'Penalty Lines',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.penalty_line_ids.ids)],
            'context': {'create': False},
        }
