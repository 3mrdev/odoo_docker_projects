from odoo import models,fields,api,_

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_logspace = fields.Boolean(default=False,string="Is Logspace")
    is_published_logspace = fields.Boolean(default=False,string="Is Published Logspace")
    document_types = fields.Many2many("logspace.document.type",domain="[('type','=','service')]")