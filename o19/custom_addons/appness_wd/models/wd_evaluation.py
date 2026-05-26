# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class CustomerEvaluation(models.Model):
    _name = 'wd.evaluation'
    _description = 'Customer Evaluation'
    _order = 'sequence, id'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, ondelete='cascade')
    scale_id = fields.Many2one('wd.standard.scale', string='Evaluation Metric')
    scale_weight = fields.Float(string='Scale Weight')
    scale_weight_matched = fields.Boolean(string='Scale Weight Matched', compute='_compute_scale_weight_matched', store=True)
    standard_id = fields.Many2one('wd.standard', string='Evaluation Category', related='scale_id.standard_id', store=True, readonly=True)
    score = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    ], string='Score', default='0')
    weighted_score = fields.Float(string='Weighted Score', compute='_compute_weighted_score', store=True)
    category_score = fields.Float(string='Category Score', compute='_compute_category_score', store=True)
    display_type = fields.Selection([('line_section', "Section")], default=False)
    name = fields.Char(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    subtotal_category_score = fields.Float(string="Subtotal", compute='_compute_subtotal_category_score', store=True)

    def reset_scale_weight(self):
        for record in self:
            record.scale_weight = record.scale_id.evaluation_weight

    @api.depends('scale_id.evaluation_weight','scale_weight')
    def _compute_scale_weight_matched(self):
        for evaluation in self:
            evaluation.scale_weight_matched = evaluation.scale_weight == evaluation.scale_id.evaluation_weight
    
    @api.depends('partner_id.evaluation_ids.score')
    def _compute_subtotal_category_score(self):
        for evaluation in self:
            domain = [
                ('partner_id', '=', evaluation.partner_id.id),
                ('standard_id', '=', evaluation.standard_id.id),
                ('display_type', '!=', 'line_section'),
            ]
            evaluation.subtotal_category_score = sum(self.search(domain).mapped('category_score'))

    @api.depends('score', 'scale_weight')
    def _compute_weighted_score(self):
        for evaluation in self:
            weighted_score = 0.0
            if evaluation.scale_id and evaluation.score:
                weighted_score = int(evaluation.score) * evaluation.scale_weight
            evaluation.weighted_score = weighted_score

    @api.depends('weighted_score', 'standard_id.weight')
    def _compute_category_score(self):
        for evaluation in self:
            category_score = 0.0
            if evaluation.standard_id:
                category_score = evaluation.weighted_score * evaluation.standard_id.weight
            else:
                category_score = 0.0
            evaluation.category_score = category_score
