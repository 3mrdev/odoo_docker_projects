from odoo import models, fields, api

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    certificate_score = fields.Char(string='Certificate Score')