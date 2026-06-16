# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class LogspaceVehicle(models.Model):
    """Logspace Vehicle - Provider Fleet Management"""
    _name = 'logspace.vehicle'
    _description = 'Logspace Vehicle'
    _order = 'provider_id, name'

    name = fields.Char(string='Vehicle Code',default='New')
    provider_id = fields.Many2one('res.partner', string='Provider',
                                   required=True, ondelete='cascade',
                                   domain=[('is_provider', '=', True)],
                                   index=True)
    vehicle_type_id = fields.Many2one('logspace.vehicle.type',
                                       string='Vehicle Type',
                                       required=True)
    zone_id = fields.Many2one('logspace.zone', string='Service Zone',
                               help='The zone this vehicle operates in')
    plate_number = fields.Char(string='Registration Number', required=True,
                               index=True)

    # Status
    is_active = fields.Boolean(string='Active', default=True)

    # Driver
    driver_id = fields.Many2one('res.partner', string='Default Driver',
                                 domain="[('parent_id', '=', provider_id), ('is_company', '=', False)]",
                                 help='Default driver assigned to this vehicle')

    # Documents (linked attachments)
    registration_doc_id = fields.Many2one('ir.attachment',
                                          string='Registration Document')
    insurance_doc_id = fields.Many2one('ir.attachment',
                                        string='Insurance Document')

    # Related fields
    provider_state = fields.Selection(related='provider_id.state',
                                        string='Provider State', store=True)

    _plate_unique = models.Constraint('unique(plate_number)', 'Vehicle registration number must be unique!')

    @api.constrains('name')
    def generate_code(self):
        for rec in self:
            if rec.name == 'New':
                rec.name = self.env['ir.sequence'].next_by_code('logspace.vehicle') or '/'

    def is_available_on_date(self, date_str):
        """Check if this vehicle is available on the given date.

        Availability depends on:
        1. Provider's working calendar (resource.calendar) - date must be a working day
        2. No existing paid booking for this vehicle on the same date or within 24h after

        Args:
            date_str: Date string in 'YYYY-MM-DD' format

        Returns:
            bool: True if vehicle is available, False otherwise
        """
        if not self.ensure_one():
            return False

        from datetime import datetime, timedelta

        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return False

        # 1. Check provider working calendar
        provider = self.provider_id
        if provider and provider.calendar_id:
            if not provider.calendar_id.work_time(target_date, target_date):
                return False

        # 2. Check for existing paid bookings on same date or within 24h buffer
        #    A vehicle becomes available 24 hours after the last booked date
        booking_date = datetime.combine(target_date, datetime.min.time())
        buffer_end = booking_date + timedelta(days=1)  # 24h after start of booking date

        existing_booking = self.env['sale.order'].sudo().search([
            ('is_logspace_order', '=', True),
            ('logspace_vehicle_id', '=', self.id),
            ('payment_status', '=', 'paid'),
            ('logspace_state', '!=', 'cancelled'),
            ('scheduled_date', '>=', booking_date),
            ('scheduled_date', '<', buffer_end),
        ], limit=1, order='scheduled_date asc')

        if existing_booking:
            return False

        return True

    @api.model
    def get_available_vehicles(self, provider_id, vehicle_type_id, zone_from_id, zone_to_id, date_str=None):
        """Get vehicles available for a provider/type/zones on a given date.

        Args:
            provider_id: Provider (res.partner) ID
            vehicle_type_id: Vehicle type ID
            zone_from_id: Pickup zone ID
            zone_to_id: Dropoff zone ID
            date_str: Optional date string 'YYYY-MM-DD'. If not provided, no date filtering.

        Returns:
            recordset of available logspace.vehicle records
        """
        if zone_from_id == zone_to_id:
            vehicle_domain = [
                ('provider_id', '=', provider_id),
                ('vehicle_type_id', '=', vehicle_type_id),
                ('is_active', '=', True),
                ('zone_id', '=', zone_from_id),
            ]
        else:
            vehicle_domain = [
                ('provider_id', '=', provider_id),
                ('vehicle_type_id', '=', vehicle_type_id),
                ('is_active', '=', True),
                '|',
                ('zone_id', '=', zone_from_id),
                ('zone_id', '=', zone_to_id),
            ]

        vehicles = self.sudo().search(vehicle_domain)

        if date_str:
            vehicles = vehicles.filtered(lambda v: v.is_available_on_date(date_str))

        return vehicles


