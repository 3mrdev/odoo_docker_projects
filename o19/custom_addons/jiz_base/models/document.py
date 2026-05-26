from odoo import models,fields,api,_
import datetime

class Document(models.Model):
    _inherit = "documents.document"

    doc_type = fields.Many2one("jiz.document.type")

    @api.constrains('doc_type')
    def check_doc_type(self):
        for rec in self:
            if rec.doc_type:
                if rec.res_model == 'crm.lead':
                    lead = self.env['crm.lead'].search([('id', '=', rec.res_id)])
                    if lead:
                        lead.check_documents()
                        # lead.compute_document_count()
                        waqf = self.env['jiz.waqf'].search([('opportunity_id', '=', rec.res_id)])
                        if waqf:
                            waqf.check_documents()
                            # waqf.compute_document_count()
                elif rec.res_model == 'jiz.waqf':
                    waqf = self.env['jiz.waqf'].search([('id', '=', rec.res_id)])
                    if waqf:
                        waqf.check_documents()
                        # waqf.compute_document_count()
                elif rec.res_model == 'helpdesk.ticket':
                    ticket = self.env['helpdesk.ticket'].search([('id', '=', rec.res_id)])
                    if ticket:
                        ticket.check_documents()
                        # ticket.compute_document_count()

    def action_open_document(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'res_model': 'documents.document',
            'target': 'new',
            'views': [(self.env.ref('documents.document_view_form').id, 'form')],
        }
        # for rec in records:
        #     action = {
        #         'type': 'ir.actions.act_window',
        #         'res_id': rec.id,
        #         'res_model': 'documents.document',
        #         'target': 'new',
        #         'views': [(env.ref('documents.document_view_form').id, 'form')],
        #     }