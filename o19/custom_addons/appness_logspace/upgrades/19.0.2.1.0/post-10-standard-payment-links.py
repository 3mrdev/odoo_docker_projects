# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api


def migrate(cr, _version):
    """Backfill Odoo's canonical sale/transaction link and harden existing orders."""
    cr.execute("""
        INSERT INTO sale_order_transaction_rel (sale_order_id, transaction_id)
        SELECT transaction.logspace_order_id, transaction.id
          FROM payment_transaction AS transaction
          JOIN sale_order AS sale_order
            ON sale_order.id = transaction.logspace_order_id
         WHERE transaction.logspace_order_id IS NOT NULL
           AND sale_order.is_logspace_order
        ON CONFLICT DO NOTHING
    """)

    env = api.Environment(cr, SUPERUSER_ID, {'logspace_skip_status_emails': True})
    env.invalidate_all()
    orders = env['sale.order'].search([('is_logspace_order', '=', True)])

    unconfirmed_orders = orders.filtered(lambda order: order.state in ('draft', 'sent'))
    unconfirmed_orders.write({
        'logspace_state': False,
        'logspace_confirmation_processed': False,
        'verification_code_pickup': False,
        'verification_code_dropoff': False,
    })

    cancelled_orders = orders.filtered(lambda order: order.state == 'cancel')
    cancelled_orders.write({
        'logspace_state': 'cancelled',
        'logspace_confirmation_processed': False,
        'verification_code_pickup': False,
        'verification_code_dropoff': False,
    })

    confirmed_orders = orders.filtered(lambda order: order.state == 'sale')
    for order in confirmed_orders:
        values = {
            'logspace_confirmation_processed': True,
            'logspace_state': order.logspace_state or 'order_received',
        }
        if not order.verification_code_pickup:
            values['verification_code_pickup'] = order._generate_verification_code()
        if order.logspace_state not in (
            'arrived_destination', 'dropoff_completed', 'grace_period', 'order_completed'
        ):
            values['verification_code_dropoff'] = False
        order.write(values)
        order._create_timeline_event(
            'order_received', 'Order received and confirmed', unique=True,
        )

    orders._sync_logspace_payment_fields()
