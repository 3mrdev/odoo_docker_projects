# -*- coding: utf-8 -*-

from odoo import models, fields

class JizUseType(models.Model):
    _name = 'jiz.use.type'
    _description = 'Use Type'

    name = fields.Char(string='Name', required=True,translate=True)
    is_rent = fields.Boolean(string='Is Rent')
