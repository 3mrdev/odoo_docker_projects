# -*- coding: utf-8 -*-

from odoo import models, fields

class JizWaqfType(models.Model):
    _name = 'jiz.waqf.type'
    _description = 'Waqf Type'

    name = fields.Char(string='Name', required=True,translate=True)
    asset_model_id = fields.Many2one('account.asset', string='Asset Type', domain="[('state', '=', 'model')]")
