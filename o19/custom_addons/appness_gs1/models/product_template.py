from odoo import models,fields,api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_rop_letter = fields.Boolean()
    is_gln_cert = fields.Boolean()
    max_gln_certs = fields.Integer(default=1)