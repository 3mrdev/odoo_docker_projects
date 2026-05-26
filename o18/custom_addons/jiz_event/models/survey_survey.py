from odoo import models, fields, api

class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    event_id = fields.Many2one('event.event', string='Event')