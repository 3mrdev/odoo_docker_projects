from odoo import models, fields, api

class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    survey_id = fields.Many2one('survey.survey', string='Survey')

    def action_generate_certificates(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generate Certificates',
            'res_model': 'jiz.gen.cert',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_channel_id': self.id},
        }