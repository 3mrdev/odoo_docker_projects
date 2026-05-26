# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class WDStandard(models.Model):
    _name = 'wd.standard'
    _description = 'Evaluation Category'

    name = fields.Char(string='Standard Name', required=True)
    weight = fields.Float(string='Weight', help="Weight for this category (e.g., 0.3 for 30%)")
    scale_ids = fields.One2many('wd.standard.scale', 'standard_id', string='Metrics')
    active = fields.Boolean(string='Active', default=True)
    
