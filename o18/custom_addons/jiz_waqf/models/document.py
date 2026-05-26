from odoo import models,fields,api

class Document(models.Model):
    _inherit = "documents.document"

    lead_id = fields.Many2one('crm.lead', string='Lead',compute='_compute_lead_id',store=True)
    waqf_id = fields.Many2one('jiz.waqf', string='Waqf',compute='_compute_lead_id',store=True)

    @api.depends('res_id','res_model')
    def _compute_lead_id(self):
        for rec in self:
            if rec.res_model == 'crm.lead':
                rec.lead_id = rec.res_id
            elif rec.res_model == 'jiz.waqf':
                rec.waqf_id = rec.res_id