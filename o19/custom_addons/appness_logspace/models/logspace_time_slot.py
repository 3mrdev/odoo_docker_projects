# -*- coding: utf-8 -*-

from odoo import models, fields, api


def _format_slot_hour(hour, minute):
    """Render an hour/minute pair the way the customer expects: '6:00 am'."""
    return '%d:%02d %s' % (hour % 12 or 12, minute, 'am' if hour < 12 else 'pm')


class LogspaceTimeSlot(models.Model):
    """Master time slots (Morning, Afternoon, Evening)"""
    _name = 'logspace.time.slot'
    _description = 'Time Slot'
    _order = 'sequence'

    # Start/end hour of each slot. The start hours feed _start_hour_by_code(),
    # which the controllers use to derive the dropoff timeframe, so the label
    # shown to the customer always matches the window the booking is actually
    # calculated for.
    TIME_WINDOWS = {
        'morning': (6, 12),
        'afternoon': (12, 18),
        'evening': (18, 24),
    }

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Selection([
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
    ], string='Code', required=True, index=True)
    sequence = fields.Integer(string='Sequence', default=10)
    label_with_time = fields.Char(
        string='Label With Time', compute='_compute_label_with_time',
        help='Customer-facing label, e.g. "Morning (6:00 am - 11:59 am)"'
    )

    _code_unique = models.Constraint(
        'unique(code)',
        'Time slot code must be unique!',
    )

    @api.depends('name', 'code')
    def _compute_label_with_time(self):
        for slot in self:
            window = self.TIME_WINDOWS.get(slot.code)
            if not window:
                slot.label_with_time = slot.name
                continue
            start_hour, end_hour = window
            slot.label_with_time = '%s (%s - %s)' % (
                slot.name,
                _format_slot_hour(start_hour, 0),
                # The window ends one minute before the next slot starts.
                _format_slot_hour(end_hour - 1, 59),
            )

    @api.model
    def _get_labels_by_code(self):
        """{code: label_with_time} for every slot - saves templates hardcoding it."""
        slots = self.sudo().search([])
        return {slot.code: slot.label_with_time for slot in slots}

    @api.model
    def _start_hour_by_code(self):
        """{code: slot start hour} for the dropoff auto-calculation."""
        return {slot.code: self.TIME_WINDOWS[slot.code][0]
                for slot in self.sudo().search([]) if slot.code in self.TIME_WINDOWS}
