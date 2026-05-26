# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LogspaceProviderTimeFrame(models.Model):
    """Provider Available Time Frames - Simple time slots per vehicle type"""
    _name = 'logspace.provider.time.frame'
    _description = 'Provider Available Time Frames'
    _rec_name = 'name'
    _order = 'partner_id, vehicle_type_id, time_start'

    # =========================================================================
    # Relations
    # =========================================================================
    partner_id = fields.Many2one(
        'res.partner',
        string='Provider',
        required=True,
        domain=[('is_provider', '=', True)],
        ondelete='cascade',
        index=True
    )
    vehicle_type_id = fields.Many2one(
        'logspace.vehicle.type',
        string='Vehicle Type',
        required=True,
        index=True
    )

    # =========================================================================
    # Time Configuration
    # =========================================================================
    time_start = fields.Float(
        string='Start Time',
        required=True,
        help='Time in hours (e.g., 8.0 = 8:00 AM, 13.5 = 1:30 PM)'
    )
    time_end = fields.Float(
        string='End Time',
        required=True,
        help='Time in hours (e.g., 12.0 = 12:00 PM)'
    )

    # =========================================================================
    # Service Type
    # =========================================================================
    is_pickup = fields.Boolean(
        string='Available for Pickup',
        default=True,
        help='This time frame is available for pickup services'
    )
    is_dropoff = fields.Boolean(
        string='Available for Dropoff',
        default=True,
        help='This time frame is available for dropoff services'
    )

    # =========================================================================
    # Computed Fields
    # =========================================================================
    name = fields.Char(
        string='Time Frame',
        compute='_compute_name',
        store=True
    )

    # =========================================================================
    # Compute Methods
    # =========================================================================
    @api.depends('time_start', 'time_end')
    def _compute_name(self):
        """Generate human-readable time frame label"""
        for tf in self:
            start_hours = int(tf.time_start)
            start_mins = int((tf.time_start % 1) * 60)
            end_hours = int(tf.time_end)
            end_mins = int((tf.time_end % 1) * 60)

            # Format: "08:00 - 12:00"
            tf.name = f"{start_hours:02d}:{start_mins:02d} - {end_hours:02d}:{end_mins:02d}"

    # =========================================================================
    # Constraints
    # =========================================================================
    @api.constrains('time_start', 'time_end')
    def _check_time_range(self):
        """Ensure end time is after start time"""
        for tf in self:
            if tf.time_end <= tf.time_start:
                raise ValidationError(_(
                    'End time must be after start time. '
                    'Current: %(start)s - %(end)s',
                    start=tf.name.split(' - ')[0] if tf.name else tf.time_start,
                    end=tf.name.split(' - ')[1] if tf.name else tf.time_end
                ))

    @api.constrains('is_pickup', 'is_dropoff')
    def _check_service_type(self):
        """Ensure at least one service type is selected"""
        for tf in self:
            if not tf.is_pickup and not tf.is_dropoff:
                raise ValidationError(_(
                    'Time frame must be available for pickup, dropoff, or both.'
                ))

    _sql_constraints = [
        ('unique_timeframe',
         'unique(partner_id, vehicle_type_id, time_start, time_end)',
         'This time frame already exists for this vehicle type!')
    ]
