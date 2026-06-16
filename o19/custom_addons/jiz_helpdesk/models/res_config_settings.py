# -*- coding: utf-8 -*-
from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    documents_ataa_settings = fields.Boolean(string="Ataa Documents", default=True)
    documents_ataa_folder = fields.Many2one(
        'documents.document',
        string="Ataa Workspace",
        default=lambda self: self.env.ref('jiz_helpdesk.documents_ataa_folder', raise_if_not_found=False),
        domain="[('type', '=', 'folder'), ('shortcut_document_id', '=', False), '|', ('company_id', '=', False), ('company_id', '=', id)]",
    )
    documents_ataa_tags = fields.Many2many('documents.tag', 'documents_ataa_tags_table')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    documents_ataa_settings = fields.Boolean(
        "Ataa",
        related='company_id.documents_ataa_settings',
        readonly=False
    )
    documents_ataa_folder = fields.Many2one(
        'documents.document',
        string='Ataa Workspace',
        related='company_id.documents_ataa_folder',
        readonly=False,
        domain="[('type', '=', 'folder'), ('shortcut_document_id', '=', False)]",
    )
    documents_ataa_tags = fields.Many2many(
        'documents.tag',
        'res_config_settings_ataa_tags_rel',
        related='company_id.documents_ataa_tags',
        readonly=False,
        string="Ataa Default Tags",
    )
