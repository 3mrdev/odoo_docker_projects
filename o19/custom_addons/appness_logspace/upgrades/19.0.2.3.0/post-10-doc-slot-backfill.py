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
    """Backfill documents.document.logspace_doc_slot for existing uploads.

    The registration flow used to identify a provider's upload by a
    `name LIKE '<human label>'` match on the underlying ir.attachment - a
    user's own filename was concatenated into that name, so the match (and the
    unlink that replaced a re-uploaded document) could hit the wrong file.
    Uploads are now identified by the slot key (vehicles_doc / company_doc /
    bank_statement) stored on the documents.document row itself.

    `post-` stage: the column is created by the registry update before this
    runs. Guarded on logspace_doc_slot IS NULL so a second run is a no-op, and
    on the attachment-name prefixes the module historically wrote
    ("<label> - <filename>"), so rows created by other apps are left alone.
    """
    if _column_exists(cr, 'documents_document', 'logspace_doc_slot'):
        cr.execute("""
            UPDATE documents_document AS dd
               SET logspace_doc_slot = CASE
                       WHEN a.name LIKE 'Vehicles Documents - %' THEN 'vehicles_doc'
                       WHEN a.name LIKE 'Company Registration - %' THEN 'company_doc'
                       WHEN a.name LIKE 'Bank Statement - %' THEN 'bank_statement'
                   END
              FROM ir_attachment AS a
             WHERE dd.attachment_id = a.id
               AND dd.partner_id IS NOT NULL
               AND dd.logspace_doc_slot IS NULL
        """)

    # Pure SQL update - drop what the registry loaded before anything reads
    # these models.
    api.Environment(cr, SUPERUSER_ID, {}).invalidate_all()
