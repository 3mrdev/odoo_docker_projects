# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    logspace_order_id = fields.Many2one(
        'sale.order', string='Logspace Order',
        domain=[('is_logspace_order', '=', True)],
        help='Linked logspace booking order',
    )

    def _post_process(self):
        """Override to handle logspace order confirmation on payment."""
        super()._post_process()

        for tx in self:
            if not tx.logspace_order_id:
                continue

            order = tx.logspace_order_id

            if tx.state == 'pending':
                # Wire transfer: order stays in draft, mark payment as pending
                if order.logspace_state == 'order_received':
                    order.write({'payment_status': 'pending'})
                _logger.info("Logspace payment pending for order %s", order.name)

            elif tx.state in ('authorized', 'done'):
                # Payment confirmed: update order payment status
                if order.payment_status != 'paid':
                    order.write({'payment_status': 'paid'})
                    _logger.info("Logspace payment confirmed for order %s", order.name)

            elif tx.state == 'cancel':
                order.write({'payment_status': 'failed'})

            elif tx.state == 'error':
                order.write({'payment_status': 'failed'})
