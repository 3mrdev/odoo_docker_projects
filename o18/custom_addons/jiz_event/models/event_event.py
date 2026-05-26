# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EventEvent(models.Model):
    _inherit = 'event.event'

    project_id = fields.Many2one('project.project', string='Project')
    survey_ids = fields.One2many('survey.survey', 'event_id', string='Surveys')
    survey_count = fields.Integer(string='Survey Count', compute='_compute_survey_count', store=True)

    @api.depends('survey_ids')
    def _compute_survey_count(self):
        for event in self:
            event.survey_count = len(event.survey_ids)

    def action_view_surveys(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'survey.survey',
            'domain': [('event_id', '=', self.id)],
            'context': {'default_event_id': self.id},
            'view_mode': 'list,form',
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals):
        res = super(EventEvent, self).create(vals)

        if res.event_type_id:
            if res.event_type_id.project_template_id:
                project = res.event_type_id.project_template_id.copy({
                    'name': f"Ataa: {res.name}",
                    'partner_id': res.organizer_id.id,
                })
                project._create_analytic_account()
                res.project_id = project.id
                
        return res