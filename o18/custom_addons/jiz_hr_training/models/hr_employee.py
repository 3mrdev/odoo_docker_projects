# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    job_number = fields.Char(string='Job Number')
    training_ids = fields.One2many('jiz.training', 'employee_id', string='Trainings')
    training_count = fields.Integer(string='Training Count', compute='_compute_training_count')

    @api.constrains('job_number')
    def _check_job_number(self):
        for employee in self:
            if employee.job_number:
                employees = self.search([('job_number', '=', employee.job_number)])
                if len(employees) > 1:
                    raise UserError(_("Job Number must be unique."))

    @api.depends('training_ids')
    def _compute_training_count(self):
        for employee in self:
            employee.training_count = len(employee.training_ids)

    def action_view_trainings(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Trainings',
            'res_model': 'jiz.training',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
