# -*- coding: utf-8 -*-

from odoo import models, fields

class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    deadline = fields.Datetime(string='Submission Deadline')
    feedback = fields.Text(string='Feedback for Student')
