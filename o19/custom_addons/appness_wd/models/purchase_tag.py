from odoo import models, fields, api

class PurchaseTag(models.Model):
    _name = 'purchase.tag'
    _description = 'Purchase Tag'

    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Color Index')
    active = fields.Boolean(string='Active', default=True)