# -*- coding: utf-8 -*-

from odoo import fields, models


class DocumentsDocument(models.Model):
    """Slot identity for the provider-registration uploads.

    The registration flow replaces a provider's per-slot document by
    re-uploading. Identity used to be a `name LIKE <human label>` on the
    underlying ir.attachment - which a user's own filename could hijack - so
    the slot key (vehicles_doc / company_doc / bank_statement) is stored here
    instead.
    """
    _inherit = 'documents.document'

    logspace_doc_slot = fields.Char(string='Logspace Doc Slot')
