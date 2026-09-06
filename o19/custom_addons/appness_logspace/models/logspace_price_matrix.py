# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class LogspacePriceMatrix(models.Model):
    """Logspace Price Matrix - Pricing Configuration by Zone and Vehicle Type"""
    _name = 'logspace.price.matrix'
    _description = 'Logspace Price Matrix'
    _order = 'provider_id, zone_from_id, zone_to_id'
    _rec_name = 'display_name'

    provider_id = fields.Many2one('res.partner', string='Provider',
                                   required=True, ondelete='cascade',
                                   domain=[('is_provider', '=', True)],
                                   index=True)
    vehicle_type_id = fields.Many2one('logspace.vehicle.type',
                                       string='Vehicle Type',
                                       required=True)

    # Zones
    zone_from_id = fields.Many2one('logspace.zone', string='From Zone',
                                    required=True, index=True)
    zone_to_id = fields.Many2one('logspace.zone', string='To Zone',
                                  required=True, index=True)

    vehicle_in_zone_count = fields.Integer(string='Number of Vehicles in Zone',
                                            compute='_compute_vehicle_in_zone_count')

    # Pricing
    distance_km = fields.Float(string='Distance (km)',
                                help='Distance between zones for reference')
    zone_distance_id = fields.Many2one(
        'logspace.zone.distance', string='Zone Distance Record',
        compute='_compute_zone_distance_id', store=False,
        help='Linked record from the zone distance matrix (if available)',
    )
    provider_price = fields.Float(string='Provider Price', required=True,
                                  default=0.0,
                                  help='What provider charges')
    platform_fee = fields.Float(string='Platform Fee',
                                 compute='_compute_platform_fee',
                                 store=True,
                                 help='Logspace commission based on provider percentage')
    customer_price = fields.Float(string='Customer Price',
                                   compute='_compute_customer_price',
                                   store=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                   default=lambda self: self.env.company.currency_id)
    is_active = fields.Boolean(string='Active', default=True, index=True)

    # Computed
    display_name = fields.Char(string='Route',
                                compute='_compute_display_name', store=True)


    @api.depends('zone_from_id', 'zone_to_id')
    def _compute_vehicle_in_zone_count(self):
        for matrix in self:
            matrix.vehicle_in_zone_count = self.env['logspace.vehicle'].search_count([
                ('zone_id', 'in', [matrix.zone_from_id.id, matrix.zone_to_id.id]),
                ('provider_id', '=', matrix.provider_id.id),
                ('vehicle_type_id', '=', matrix.vehicle_type_id.id),
            ])

    @api.depends('provider_price', 'provider_id.platform_fee_percentage')
    def _compute_platform_fee(self):
        for matrix in self:
            percentage = matrix.provider_id.platform_fee_percentage or 0.0
            # If percentage is entered directly as 10.0 (legacy) divide by 100
            # If entered via percentage widget, it is already a fraction (e.g. 0.1)
            multiplier = percentage / 100.0 if percentage > 1.0 else percentage
            matrix.platform_fee = matrix.provider_price * multiplier

    @api.depends('provider_price', 'platform_fee')
    def _compute_customer_price(self):
        for matrix in self:
            matrix.customer_price = matrix.provider_price + matrix.platform_fee

    @api.depends('zone_from_id', 'zone_to_id')
    def _compute_display_name(self):
        for matrix in self:
            from_name = matrix.zone_from_id.name or ''
            to_name = matrix.zone_to_id.name or ''
            matrix.display_name = f"{from_name} → {to_name}"

    _price_unique = models.Constraint(
        'unique(provider_id, vehicle_type_id, zone_from_id, zone_to_id)',
        'Price already exists for this provider, vehicle type, and route!'
    )

    @api.depends('zone_from_id', 'zone_to_id')
    def _compute_zone_distance_id(self):
        """Link to the matching zone distance record if one exists."""
        ZoneDist = self.env['logspace.zone.distance']
        for matrix in self:
            if matrix.zone_from_id and matrix.zone_to_id:
                rec = ZoneDist.search([
                    ('zone_from_id', '=', matrix.zone_from_id.id),
                    ('zone_to_id', '=', matrix.zone_to_id.id),
                ], limit=1)
                matrix.zone_distance_id = rec.id if rec else False
            else:
                matrix.zone_distance_id = False

    @api.onchange('zone_from_id', 'zone_to_id')
    def _onchange_zones(self):
        """Auto-fill distance_km from the zone distance matrix."""
        if self.zone_from_id and self.zone_to_id:
            ZoneDist = self.env['logspace.zone.distance']
            distance = ZoneDist.get_distance(self.zone_from_id, self.zone_to_id)
            self.distance_km = distance

    def action_open_zone_setup_wizard(self):
        """Open the zone setup wizard from the price matrix list view."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'logspace.zone.setup.wizard',
            'view_mode': 'form',
            'target': 'new',
            'name': _('Setup Zones'),
        }
