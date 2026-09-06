# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LogspaceProviderFleetSummary(models.Model):
    """Provider Fleet Summary - Capacity by Vehicle Type"""
    _name = 'logspace.provider.fleet.summary'
    _description = 'Provider Fleet Summary by Vehicle Type'
    _rec_name = 'vehicle_type_id'
    _order = 'partner_id, vehicle_type_id'

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
    # Fleet Data
    # =========================================================================
    fleet_count = fields.Integer(
        string='Fleet Count',
        required=True,
        default=1,
        help='Number of vehicles of this type in the fleet'
    )
    capacity_tons = fields.Float(
        string='Capacity (Tons)',
        help='Maximum weight capacity in tons'
    )
    dimensions = fields.Char(
        string='Dimensions',
        help='Storage dimensions, e.g., 300x200x150 cm (L x W x H)'
    )

    # =========================================================================
    # Related Fields
    # =========================================================================
    partner_state = fields.Selection(
        related='partner_id.state',
        string='Provider State',
        store=True
    )

    # =========================================================================
    # Constraints
    # =========================================================================
    _sql_constraints = [
        ('unique_provider_vehicle_type',
         'unique(partner_id, vehicle_type_id)',
         'Fleet summary for this vehicle type already exists!')
    ]

    # =========================================================================
    # Onchange Methods
    # =========================================================================
    @api.onchange('vehicle_type_id')
    def _onchange_vehicle_type(self):
        """Auto-populate default capacity from vehicle type"""
        if self.vehicle_type_id and not self.capacity_tons:
            # Convert kg to tons
            self.capacity_tons = self.vehicle_type_id.default_capacity_kg / 1000.0
