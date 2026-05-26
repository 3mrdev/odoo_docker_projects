# -*- coding: utf-8 -*-

from odoo import models, fields


class HrJob(models.Model):
    """Extend hr.job for Logspace contact roles visibility in portal"""
    _inherit = 'hr.job'

    show_in_portal = fields.Boolean(
        string='Show in Portal',
        default=False,
        help='If checked, contacts with this job position will be visible to customers in the portal'
    )
