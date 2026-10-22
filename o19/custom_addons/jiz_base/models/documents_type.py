# -*- coding: utf-8 -*-

from odoo import models, fields

class DocumentType(models.Model):
    _name = "jiz.document.type"
    _description = "Document Type"
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    is_mandatory = fields.Boolean()
    active = fields.Boolean(default=True)
    type = fields.Selection([
        ('ataa', 'Ataa'),
        ('waqf', 'Waqf'),
    ], required=True)