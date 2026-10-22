# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api


def _column_exists(cr, table, column):
    cr.execute("""
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = %s
           AND column_name = %s
         LIMIT 1
    """, (table, column))
    return bool(cr.fetchone())


def migrate(cr, _version):
    """Move vehicle types onto the new category model and flag existing provider bills.

    data/data_vehicle_types.xml is noupdate="1", so the seeded rows never pick up
    the new category_id on their own. Odoo drops no columns on upgrade
    (_check_removed_columns only relaxes NOT NULL), so the former `category`
    Selection is still readable here - `post-` stage, after the registry update,
    which is when logspace_vehicle_category and category_id already exist.

    The new sale.order payout/commission fields need no backfill: they are
    stored *computed* fields, and _auto_init queues every existing record for
    computation when it creates their columns (odoo/orm/models.py:3232-3241).
    """
    if _column_exists(cr, 'logspace_vehicle_type', 'category'):
        # The old Selection stored exactly the codes the new category records
        # are seeded with, so the join is a straight code match. Guarded on
        # category_id IS NULL so a second run - or a type an admin has already
        # re-categorised by hand - is left alone.
        cr.execute("""
            UPDATE logspace_vehicle_type AS vt
               SET category_id = cat.id
              FROM logspace_vehicle_category AS cat
             WHERE cat.code = vt.category
               AND vt.category_id IS NULL
               AND vt.category IS NOT NULL
        """)

    # Provider bills created before is_logspace_provider_bill existed would be
    # invisible in the new Logspace > Sales > Provider Bills menu. COALESCE
    # because a freshly created boolean column can still hold NULL.
    if _column_exists(cr, 'account_move', 'is_logspace_provider_bill'):
        cr.execute("""
            UPDATE account_move
               SET is_logspace_provider_bill = TRUE
             WHERE id IN (
                    SELECT logspace_provider_bill_id
                      FROM sale_order
                     WHERE logspace_provider_bill_id IS NOT NULL
                   )
               AND COALESCE(is_logspace_provider_bill, FALSE) = FALSE
        """)

    # Both updates went straight to the tables, so drop whatever the registry
    # loaded during the upgrade before anything else reads these models.
    api.Environment(cr, SUPERUSER_ID, {}).invalidate_all()
