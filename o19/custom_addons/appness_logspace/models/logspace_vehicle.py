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

    # States at which a paid booking releases the vehicle for new bookings
    BOOKED_RELEASE_STATES = ('grace_period', 'order_completed')

    def is_available_on_date(self, date_str=None):
        """Check if this vehicle is bookable.

        A vehicle with a paid, non-cancelled booking is hidden from search
        results until that order reaches the grace period (or is completed or
        cancelled). Additionally, when a date is given, it must fall on the
        provider's working calendar.

        Args:
            date_str: Optional date string in 'YYYY-MM-DD' format

        Returns:
            bool: True if vehicle is available, False otherwise
        """
        if not self.ensure_one():
            return False

        from datetime import datetime

        # 1. A paid booking keeps the vehicle out of search results until the
        #    order reaches the grace period / is completed / is cancelled.
        active_booking = self.env['sale.order'].sudo().search([
            ('is_logspace_order', '=', True),
            ('logspace_vehicle_id', '=', self.id),
            ('payment_status', '=', 'paid'),
            ('logspace_state', 'not in', list(self.BOOKED_RELEASE_STATES) + ['cancelled']),
        ], limit=1)

        if active_booking:
            return False

        if not date_str:
            return True

        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return False

        # 2. Check provider working calendar (weekday only, not time)
        provider = self.provider_id
        if provider and provider.calendar_id:
            weekday = target_date.weekday()  # 0=Mon, 6=Sun
            calendar = provider.calendar_id
            # Check if this weekday has attendance entries
            if calendar.two_weeks_calendar:
                week_type = str(
                    self.env['resource.calendar.attendance'].get_week_type(target_date)
                )
                working_day = bool(calendar.attendance_ids.filtered(
                    lambda a: not a.display_type
                    and int(a.dayofweek) == weekday
                    and a.week_type == week_type
                ))
            else:
                working_day = bool(calendar.attendance_ids.filtered(
                    lambda a: not a.display_type and int(a.dayofweek) == weekday
                ))
            if not working_day:
                return False

        return True

    @api.model
    def get_available_vehicles(self, provider_id, vehicle_type_id, zone_from_id, zone_to_id=None, date_str=None):
        """Get vehicles available for a provider/type in the pickup zone on a given date.

        Vehicle matching uses FROM-ZONE ONLY:
        - Vehicle must be in the pickup zone (with hierarchy expansion)
        - This is realistic: vehicle needs to physically reach the pickup location
        - The to-zone is handled by the price matrix (route availability & pricing)

        Args:
            provider_id: Provider (res.partner) ID
            vehicle_type_id: Vehicle type ID
            zone_from_id: Pickup zone ID (vehicle must be in this zone hierarchy)
            zone_to_id: Dropoff zone ID (kept for API compatibility, not used for vehicle matching)
            date_str: Optional date string 'YYYY-MM-DD'. If not provided, only the
                booked-vehicle rule applies (no working-calendar filtering).

        Returns:
            recordset of available logspace.vehicle records
        """
        # Expand pickup zone bidirectionally: ancestors (UP) + descendants (DOWN)
        # - District search finds parent city vehicles
        # - City search finds child district vehicles
        zone_from_obj = self.env['logspace.zone'].sudo().browse(zone_from_id)
        zone_from_ids = zone_from_obj._get_zone_hierarchy_ids()

        # Vehicle must be in the pickup zone (from-zone only)
        vehicle_domain = [
            ('provider_id', '=', provider_id),
            ('vehicle_type_id', '=', vehicle_type_id),
            ('is_active', '=', True),
            ('zone_id', 'in', zone_from_ids),
        ]

        vehicles = self.sudo().search(vehicle_domain)

        return vehicles.filtered(lambda v: v.is_available_on_date(date_str))


