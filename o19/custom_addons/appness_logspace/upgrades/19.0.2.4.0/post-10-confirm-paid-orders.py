# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api


def migrate(cr, _version):
    """Confirm paid logspace orders the old payment flow left as quotations.

    Older versions created the payment transaction with only
    `logspace_order_id` and never linked it into `sale_order_ids`, so core
    Odoo's auto-confirm (`_check_amount_and_confirm_order`, which only looks
    at `sale_order_ids`) never fired and paid orders stayed draft/sent. Those
    transactions are already post-processed, so deploying the fixed
    `_post_process` alone will never revisit them - they are confirmed here.

    Historical orders are confirmed silently (no `send_email` context): the
    customer already received his payment confirmation; a confirmation mail
    for an order from weeks ago would be noise. Going forward, payments
    confirm through the standard flow and mail normally.

    Orders are selected from both link paths - the canonical
    sale_order_transaction_rel table and the legacy logspace_order_id column -
    so this runs correctly even on a database that never received the
    19.0.2.1.0 rel-link backfill. Idempotent: orders already in 'sale' are
    skipped and `_sync_logspace_payment_fields` re-derives the same status on
    a second run.
    """
    # Canonicalize the legacy links first (same statement as 19.0.2.1.0), so
    # `_sync_logspace_payment_fields` below sees the transactions through
    # `transaction_ids` even when the earlier backfill never ran.
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

    cr.execute("""
        SELECT DISTINCT so.id
          FROM sale_order so
          JOIN payment_transaction pt
            ON pt.logspace_order_id = so.id
         WHERE so.is_logspace_order
           AND pt.state IN ('authorized', 'done')
        UNION
        SELECT DISTINCT so.id
          FROM sale_order so
          JOIN sale_order_transaction_rel rel
            ON rel.sale_order_id = so.id
          JOIN payment_transaction pt
            ON pt.id = rel.transaction_id
         WHERE so.is_logspace_order
           AND pt.state IN ('authorized', 'done')
    """)
    order_ids = [row[0] for row in cr.fetchall()]

    env = api.Environment(cr, SUPERUSER_ID, {'logspace_skip_status_emails': True})
    orders = env['sale.order'].browse(order_ids)
    env.invalidate_all()

    orders.filtered(
        lambda order: order.state in ('draft', 'sent')
    ).action_confirm()

    orders._sync_logspace_payment_fields()
