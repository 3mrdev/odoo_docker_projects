# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class JizStandard(models.Model):
    _name = 'jiz.standard'
    _description = 'Evaluation Category'

    name = fields.Char(string='Name', required=True)
    weight = fields.Float(string='Weight', help="Weight for this category (e.g., 0.3 for 30%)")
    scale_ids = fields.One2many('jiz.standard.scale', 'standard_id', string='Metrics')
    active = fields.Boolean(string='Active', default=True)
    
