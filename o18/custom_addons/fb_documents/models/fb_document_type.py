from odoo import models, fields

class FbDocumentType(models.Model):
    _name = 'fb.document.type'
    _description = 'Document Type'

    name = fields.Char(string='Name', required=True)