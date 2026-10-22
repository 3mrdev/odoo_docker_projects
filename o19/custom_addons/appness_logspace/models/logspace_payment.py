# -*- coding: utf-8 -*-

from odoo import Command, fields, models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    logspace_order_id = fields.Many2one(
        'sale.order', string='Logspace Order',
        domain=[('is_logspace_order', '=', True)],
        copy=False,
        index=True,
        help='Linked logspace booking order',
    )

    def _post_process(self):
        """Keep legacy links compatible, then defer confirmation entirely to Odoo sale."""
        legacy_transactions = self.sudo().filtered(
            lambda tx: tx.logspace_order_id and tx.logspace_order_id not in tx.sale_order_ids
        )
        for transaction in legacy_transactions:
            transaction.write({
                'sale_order_ids': [Command.link(transaction.logspace_order_id.id)],
            })

        result = super()._post_process()

        transactions_sudo = self.sudo()
        logspace_orders = transactions_sudo.mapped('sale_order_ids').filtered(
            'is_logspace_order'
        )
        logspace_orders |= transactions_sudo.mapped('logspace_order_id').filtered(
            'is_logspace_order'
        )
        logspace_orders.sudo()._sync_logspace_payment_fields()
        return result
