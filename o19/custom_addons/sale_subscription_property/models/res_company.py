from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    show_properties_features = fields.Boolean()
