# -*- coding: utf-8 -*-

from odoo import models, fields, api

class JizTraining(models.Model):
    _name = 'jiz.training'
    _description = 'Employee Training'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Training Title', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    provider_id = fields.Many2one('res.partner', string='Provider')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    certification_indicator = fields.Boolean(string='Provides Certification')
    status = fields.Selection([
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='planned', tracking=True)
    training_type_id = fields.Many2one('jiz.training.type', string='Training Type')

    def action_start(self):
        self.write({'status': 'in_progress'})

    def action_complete(self):
        self.write({'status': 'completed'})

    def action_cancel(self):
        self.write({'status': 'cancelled'})

    def action_reset_to_planned(self):
        self.write({'status': 'planned'})
