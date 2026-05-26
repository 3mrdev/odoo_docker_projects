# -*- coding: utf-8 -*-
from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    documents_waqf_settings = fields.Boolean(string="Waqf Documents", default=True)
    documents_waqf_folder = fields.Many2one(
        'documents.document',
        string="Waqf Workspace",
        default=lambda self: self.env.ref('jiz_waqf.documents_waqf_folder', raise_if_not_found=False),
        domain="[('type', '=', 'folder'), ('shortcut_document_id', '=', False), '|', ('company_id', '=', False), ('company_id', '=', id)]",
    )
    documents_waqf_tags = fields.Many2many('documents.tag', 'documents_waqf_tags_table')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    documents_waqf_settings = fields.Boolean(
        "Waqf",
        related='company_id.documents_waqf_settings',
        readonly=False
    )
    documents_waqf_folder = fields.Many2one(
        'documents.document',
        string='Waqf Workspace',
        related='company_id.documents_waqf_folder',
        readonly=False,
        domain="[('type', '=', 'folder'), ('shortcut_document_id', '=', False)]",
    )
    documents_waqf_tags = fields.Many2many(
        'documents.tag',
        'res_config_settings_waqf_tags_rel',
        related='company_id.documents_waqf_tags',
        readonly=False,
        string="Waqf Default Tags",
    )
