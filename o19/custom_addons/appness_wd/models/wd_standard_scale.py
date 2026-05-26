# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class WDStandardScale(models.Model):
    _name = 'wd.standard.scale'
    _description = 'Evaluation Metric'

    name = fields.Char(string='Metric', required=True)
    standard_id = fields.Many2one('wd.standard', string='Category', required=True, ondelete='cascade')
    evaluation_weight = fields.Float(string='Weight', help="Weight for this metric within its category (e.g., 0.5 for 50%)")
    active = fields.Boolean(string='Active', default=True)

    @api.constrains('standard_id', 'evaluation_weight')
    def _check_scale_weights(self):
        for rec in self:
            total_weight = sum(rec.standard_id.scale_ids.mapped('evaluation_weight'))
            if total_weight > 1:
                raise UserError("Total weight of metrics inside a category must be less than or equal to 1")