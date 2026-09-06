# -*- coding: utf-8 -*-

from odoo import models, fields


class LogspaceTimeSlot(models.Model):
    """Master time slots (Morning, Afternoon, Evening)"""
    _name = 'logspace.time.slot'
    _description = 'Time Slot'
    _order = 'sequence'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Selection([
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
    ], string='Code', required=True, index=True)
    sequence = fields.Integer(string='Sequence', default=10)

    _sql_constraints = [
        ('unique_code', 'unique(code)', 'Time slot code must be unique!')
    ]
