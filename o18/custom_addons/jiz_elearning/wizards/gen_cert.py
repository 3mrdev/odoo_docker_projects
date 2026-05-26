from odoo import models, fields, api
from odoo.exceptions import UserError

class GenCert(models.TransientModel):
    _name = 'jiz.gen.cert'
    _description = 'Generate Certificate'

    channel_id = fields.Many2one('slide.channel', string='Channel')
    survey_id = fields.Many2one('survey.survey', string='Survey',related='channel_id.survey_id',store=True)
    new_scores_ids = fields.One2many('jiz.gen.cert.scores', 'gen_cert_id', string='New Scores')

    @api.onchange('survey_id')
    def _onchange_survey_id(self):
        for rec in self:
            new_students_list = []

            new_students_list = self.get_student_scores(rec)

            rec.new_scores_ids = [(0, 0, student) for student in new_students_list]

    def action_generate_certificates(self):
        for rec in self:
            certificates = []
            # raise UserError(f"{','.join(str(score.student_id.id) for score in rec.new_scores_ids)}")
            for score in rec.new_scores_ids:
                if score.student_id:
                    certificate = self.env['survey.user_input'].search([('partner_id', '=', score.student_id.id), ('survey_id', '=', rec.survey_id.id)])
                    if not certificate:
                        if score.score:
                            new_cert_id = self.env['survey.user_input'].create({
                                'partner_id': score.student_id.id,
                                'survey_id': rec.survey_id.id,
                                'certificate_score': score.score,
                                'scoring_success': True,
                                'state': 'done',
                            })
                            certificates.append(new_cert_id)
                        else:
                            raise UserError(f"Score is empty for student {score.student_id.name}")
            
            if certificates:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Certificates Generated',
                    'res_model': 'survey.user_input',
                    'view_mode': 'list,form',
                    'domain': [('id', 'in', [cert.id for cert in certificates])],
                    'target': 'current',
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'No Certificates Generated',
                        'message': 'No new certificates were generated.',
                        'type': 'warning',
                        'sticky': False,
                    },
                }

    def view_old_certificates(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Old Certificates',
                'res_model': 'survey.user_input',
                'view_mode': 'list,form',
                'domain': [('survey_id', '=', rec.survey_id.id)],
                'target': 'current',
            }

    def get_student_scores(self, rec):
        all_students_list = []
        new_students_list = []

        for student in rec.channel_id.partner_ids:
            all_students_list.append({
                'student_id': student.id,
                'score': False
            })
        
        for student in all_students_list:
            certificates = self.env["survey.user_input"].sudo().search([('survey_id', '=', rec.survey_id.id),('partner_id', '=', student['student_id'])])
            if not certificates:
                new_students_list.append({'student_id': student['student_id'],'score': False})

        return new_students_list

class Scores(models.TransientModel):
    _name = 'jiz.gen.cert.scores'
    _description = 'Generate Certificate Scores'
    
    gen_cert_id = fields.Many2one('jiz.gen.cert', string='Generate Certificate')
    student_id = fields.Many2one('res.partner', string='Student')
    score = fields.Char(string='Score')