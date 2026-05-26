from odoo import models, fields

class Document(models.Model):
    _inherit = "documents.document"

    ref = fields.Char(string="Reference")
    issued_by = fields.Many2one("res.partner", string="Issued By")
    issue_date = fields.Date(string="Issuance Date")
    expiry_date = fields.Date(string="Expiration Date")
    remarks = fields.Html(string="Remarks")