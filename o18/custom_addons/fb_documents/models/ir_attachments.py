from odoo import fields, models,api

class IrAttachments(models.Model):
    _inherit = 'ir.attachment'

    doc_type = fields.Many2one('fb.document.type', string='Document Type')
    department = fields.Many2one('hr.department', string='Department')
    sequence = fields.Char(string='Sequence')

    @api.model_create_multi
    def create(self, vals):
        res = super(IrAttachments, self).create(vals)
        if not res.sequence:
            res.sequence = self.env['ir.sequence'].next_by_code('fb.document')
        return res