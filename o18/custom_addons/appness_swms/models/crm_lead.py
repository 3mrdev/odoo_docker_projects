from odoo import models,fields,api,_

class CRMLead(models.Model):
    _inherit = "crm.lead"

    is_swms = fields.Boolean()
    sponsered_qty = fields.Integer()
    is_available = fields.Boolean(compute="_compute_is_available",store=True)
    lines = fields.One2many("swms.service.line", "lead")
    
    @api.depends("sponsered_qty","lines")
    def _compute_is_available(self):
        for rec in self:
            rec.is_available = False
            if rec.sponsered_qty > len(rec.lines):
                rec.is_available = True