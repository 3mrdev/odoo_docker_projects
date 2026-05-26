from odoo import models,fields,api,_

class PersonalProperty(models.Model):
    _name = "swms.property"
    _description = "Personal Property"
    _rec = "doc_type"

    doc_type = fields.Many2one("swms.document.type",domain="[('type','=','property')]",string="Type")
    ownership_date = fields.Date()
    expire_date = fields.Date()
    partner_id = fields.Many2one("res.partner")
