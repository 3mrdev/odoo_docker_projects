# -*- coding: utf-8 -*-

from odoo import models, fields

class PropertyType(models.Model):
    _name = 'hrb.property.type'
    _description = 'Property Type'

    name = fields.Char(string='Name', required=True,translate=True)
