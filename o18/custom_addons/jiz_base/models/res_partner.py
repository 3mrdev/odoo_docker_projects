# -*- coding: utf-8 -*-

from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    civil_number = fields.Char(string='Civil Number')
    date_of_birth = fields.Date(string='Date of Birth')
