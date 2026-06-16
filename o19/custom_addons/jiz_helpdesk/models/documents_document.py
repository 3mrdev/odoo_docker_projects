# -*- coding: utf-8 -*-

from odoo import models, fields, api

class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    ataa_id = fields.Many2one('helpdesk.ticket', string='Ataa Request',compute='_compute_ataa_id',store=True)

    @api.depends('res_id','res_model')
    def _compute_ataa_id(self):
        for rec in self:
            if rec.res_model == 'helpdesk.ticket':
                rec.ataa_id = rec.res_id
