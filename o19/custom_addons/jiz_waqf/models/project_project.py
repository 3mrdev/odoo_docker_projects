from odoo import models, fields, api, _

class ProjectProject(models.Model):
    _inherit = 'project.project'

    waqf_id = fields.Many2one('jiz.waqf', string='Waqf')
