# -*- coding: utf-8 -*-

from odoo import models, fields

class EventType(models.Model):
    _inherit = 'event.type'

    project_template_id = fields.Many2one('project.project', string='Project Template',
        help="Select a project template to be used when a new event is created from this template.")