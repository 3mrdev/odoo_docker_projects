# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from . import helpers

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    form_document = fields.Binary(string='Form Document')
    document_count = fields.Integer(compute='compute_document_count', string='Documents',store=True)
    documents = fields.One2many('documents.document', 'lead_id', string='Documents')
    noti_documents = fields.Text()
    waqf_ids = fields.One2many('jiz.waqf', 'opportunity_id', string='Waqfs')
    waqf_count = fields.Integer(string='Waqf Count', compute='_compute_waqf_count')
    city_id = fields.Many2one('res.city', string='City', domain="[('state_id', '=?', state_id)]")
    area_id = fields.Many2one('res.area', string='Area', domain="[('city_id', '=?', city_id)]")
    country_enforce_cities = fields.Boolean(related='country_id.enforce_cities')
    land_number = fields.Char(string='Land Number')
    waqf_valuation = fields.Float(string='Waqf Valuation')
    waqf_type = fields.Selection([
        ('cash', 'Cash'),
        ('in_kind', 'In Kind'),
    ], string='Waqf Type',related='team_id.waqf_type', store=True)
    waqf_type_id = fields.Many2one('jiz.waqf.type', string='Waqf Property Type')
    use_type_id = fields.Many2one('jiz.use.type', string='Use Type')
    use_type_is_rent = fields.Boolean(related='use_type_id.is_rent', store=True)
    thank_you_message_sent = fields.Boolean(string='Thank You Message Sent ?')
    asset_model_id = fields.Many2one('account.asset', string='Asset Type', domain="[('state', '=', 'model')]",related='waqf_type_id.asset_model_id',store=True)

    @api.constrains('document_count','stage_id','waqf_type')
    def check_documents(self):
        for rec in self:
            if rec.waqf_type == 'in_kind':
                vdoc = helpers.validate_documents(self)
                if vdoc['types']:
                    rec.noti_documents = _("Missing Documents:")+f""" \n{vdoc['types']}"""
                else:
                    rec.noti_documents = False

    @api.depends('waqf_ids')
    def _compute_waqf_count(self):
        for lead in self:
            lead.waqf_count = len(lead.waqf_ids)

    @api.depends("documents")
    def compute_document_count(self):
        for record in self:
            record.document_count = len(record.documents)

    def _get_document_folder(self):
        return self.company_id.documents_waqf_folder

    def _get_document_tags(self):
        return self.company_id.documents_waqf_tags

    def _check_create_documents(self):
        return self.company_id.documents_waqf_settings and super()._check_create_documents()

    def action_open_attachments(self):
        self.ensure_one()
        if not self.company_id.documents_waqf_settings:
            return True
        waqf_folder = self._get_document_folder()
        waqf_tags = self._get_document_tags()
        action = self.env['ir.actions.act_window']._for_xml_id('documents.document_action')
        action['domain'] = [
            '|',
                ('type', '=', 'folder'),
                '&',
                    ('res_model', '=', self._name),
                    ('res_id', '=', self.id),
        ]
        action['context'] = {
            'default_res_id': self.id,
            'default_res_model': self._name,
            'searchpanel_default_folder_id': waqf_folder.id,
            'searchpanel_default_tag_ids': waqf_tags.ids,
        }
        return action

    def action_create_waqf(self):
        self.ensure_one()
        
        if self.waqf_type == 'in_kind':
            vdoc = helpers.validate_documents(self)
            if vdoc['types']:
                raise UserError(_("Missing Documents:")+f""" \n{vdoc['types']}""")

        if self.waqf_valuation <= 0:
            raise UserError(_("You cannot submit a Waqf with a valuation of zero or less."))

        if not self.asset_model_id:
            raise UserError(_("You cannot submit a Waqf without an asset model. Please add one in the waqf type"))
            

        waqf = self.env['jiz.waqf'].create({
            'name': self.name,
            'waqf_endower_contact_id': self.partner_id.id,
            'opportunity_id': self.id,
            'waqf_valuation': self.waqf_valuation,
            'street': self.street,
            'street2': self.street2,
            'zip': self.zip,
            'city': self.city,
            'state_id': self.state_id.id,
            'country_id': self.country_id.id,
            'city_id': self.city_id.id,
            'area_id': self.area_id.id,
            'waqf_type_id': self.waqf_type_id.id,
            'use_type_id': self.use_type_id.id,
            'asset_model_id': self.asset_model_id.id,
            'land_number':self.land_number,
            'tag_ids': self.tag_ids.ids,
        })

        if self.asset_model_id.is_automated:
            waqf.action_submit()
            waqf.action_create_asset()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Waqf',
            'res_model': 'jiz.waqf',
            'res_id': waqf.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_waqfs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Waqfs',
            'res_model': 'jiz.waqf',
            'view_mode': 'list,form',
            'domain': [('opportunity_id', '=', self.id)],
            'context': {'default_opportunity_id': self.id},
        }