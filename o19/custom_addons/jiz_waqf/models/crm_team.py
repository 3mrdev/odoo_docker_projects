from odoo import models, fields, api

class CrmTeam(models.Model):
    _inherit = 'crm.team'
    
    waqf_type = fields.Selection([
        ('cash', 'Cash'),
        ('in_kind', 'In Kind'),
    ], string='Waqf Type')