from odoo import models, fields, api, _


class HRSalaryAttachment(models.Model):
    _inherit = 'hr.salary.attachment'

    approval_request_id = fields.Many2one('approval.request', string='Approval Request')
