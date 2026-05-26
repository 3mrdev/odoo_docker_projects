from odoo import models, fields

class Area(models.Model):
    _name = "res.area"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Area"
    
    name = fields.Char(string='Name',translate=True,required=True)
    city_id = fields.Many2one("res.city", string="City")