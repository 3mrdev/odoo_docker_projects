# -*- coding: utf-8 -*-

from odoo import models, fields

class JizTrainingType(models.Model):
    _name = 'jiz.training.type'
    _description = 'Training Type'

    name = fields.Char(string='Name', required=True)
