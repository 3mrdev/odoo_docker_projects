from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    allow_companies_only = fields.Boolean()
    tag_as_manufacturer = fields.Boolean()
    default_industry_on_partner_creation = fields.Many2one("res.partner.industry")
    default_rop_letter_visual_guide = fields.Binary()
    show_rop_letter = fields.Boolean()
    show_gs1_cert = fields.Boolean()
    manager_signature = fields.Many2one('res.users', string='Manager Signature')
    phone2 = fields.Char()
