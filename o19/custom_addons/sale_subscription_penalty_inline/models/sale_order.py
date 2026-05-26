# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _cron_add_penalty_lines(self):
        """
        Daily cron to find subscription invoices with late payments
        and add penalty lines to them.
        
        Process:
        - Find all unpaid subscription invoices past their period end
        - Check if penalty is due (first time or yearly anniversary)
        - Add penalty line to the invoice
        """
        # Get penalty amount from settings
        penalty_amount = float(self.env['ir.config_parameter'].sudo().get_param(
            'sale_subscription_penalty_inline.penalty_amount', default=0.0
        ))
        
        if penalty_amount <= 0:
            _logger.info("Penalty amount not configured. Skipping penalty line addition.")
            return 0
        
        # Get penalty product from settings
        penalty_product_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'sale_subscription_penalty_inline.penalty_product_id', default=0
        ))
        
        if not penalty_product_id:
            _logger.warning("Penalty product not configured. Skipping penalty line addition.")
            return 0
        
        penalty_product = self.env['product.product'].browse(penalty_product_id)
        if not penalty_product.exists():
            _logger.error("Configured penalty product (ID: %s) does not exist.", penalty_product_id)
            return 0
        
        # Find all active subscriptions
        subscriptions = self.search([
            ('is_subscription', '=', True),
            ('subscription_state', 'in', ['3_progress', '4_paused']),
        ])
        
        penalty_count = 0
        for subscription in subscriptions:
            # Get all invoices from this subscription that need penalties
            invoices_needing_penalty = subscription.invoice_ids.filtered(
                lambda inv: inv._should_add_penalty_line()
            )
            
            for invoice in invoices_needing_penalty:
                try:
                    penalty_line = invoice._add_penalty_invoice_line(penalty_product, penalty_amount)
                    if penalty_line:
                        penalty_count += 1
                        _logger.info(
                            "Added penalty line to invoice %s (Subscription: %s)",
                            invoice.name,
                            subscription.name
                        )
                        # invoice._compute_amount()
                        # invoice._compute_tax_totals()
                        invoice.button_draft()
                        invoice.action_post()
                except Exception as e:
                    _logger.error(
                        "Error adding penalty line to invoice %s: %s",
                        invoice.name,
                        str(e)
                    )
                    continue
        
        _logger.info("Penalty line cron completed. Added %d penalty lines.", penalty_count)
        return penalty_count
