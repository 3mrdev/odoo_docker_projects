# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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

    @api.model
    def _validate_booking_selection(
        self, *, matrix_id, provider_id, vehicle_type_id, zone_from_id,
        zone_to_id, vehicle_id, pickup_date=None,
    ):
        """Resolve a client selection to active, mutually consistent records.

        Browser query parameters and session values are only identifiers. Prices are
        always read from the selected matrix after every relationship is verified.
        """
        matrix = self.sudo().browse(matrix_id).exists()
        if not matrix or not matrix.is_active:
            raise ValidationError(_('The selected route price is no longer available.'))

        provider = matrix.provider_id
        if (
            provider.id != provider_id
            or not provider.active
            or not provider.is_provider
            or provider.state != 'approved'
        ):
            raise ValidationError(_('The selected logistics provider is not available.'))

        vehicle_type = matrix.vehicle_type_id
        if vehicle_type.id != vehicle_type_id or not vehicle_type.active:
            raise ValidationError(_('The selected vehicle type is not available.'))

        zone_from = self.env['logspace.zone'].sudo().browse(zone_from_id).exists()
        zone_to = self.env['logspace.zone'].sudo().browse(zone_to_id).exists()
        if not zone_from or not zone_from.active or not zone_to or not zone_to.active:
            raise ValidationError(_('The selected pickup or drop-off zone is not available.'))
        if (
            matrix.zone_from_id.id not in zone_from._get_zone_hierarchy_ids()
            or matrix.zone_to_id.id not in zone_to._get_zone_hierarchy_ids()
        ):
            raise ValidationError(_('The selected price does not match this route.'))

        vehicle = self.env['logspace.vehicle'].sudo().browse(vehicle_id).exists()
        pickup_zone_ids = zone_from._get_zone_hierarchy_ids()
        if (
            not vehicle
            or not vehicle.is_active
            or vehicle.provider_id != provider
            or vehicle.vehicle_type_id != vehicle_type
            or vehicle.zone_id.id not in pickup_zone_ids
        ):
            raise ValidationError(_('The selected vehicle does not match this booking.'))
        if not vehicle.is_available_on_date(pickup_date):
            raise ValidationError(_('The selected vehicle is not available.'))

        if (
            matrix.customer_price <= 0
            or not matrix.currency_id.active
            or matrix.currency_id != self.env.company.currency_id
        ):
            raise ValidationError(_('The selected route has an invalid price configuration.'))

        return {
            'matrix': matrix,
            'provider': provider,
            'vehicle_type': vehicle_type,
            'zone_from': zone_from,
            'zone_to': zone_to,
            'vehicle': vehicle,
            'price': matrix.customer_price,
            'currency': matrix.currency_id,
        }

    def _get_validated_booking_addons(self, addon_ids):
        """Return offered add-ons and server-side prices for this matrix."""
        self.ensure_one()
        normalized_ids = []
        for addon_id in addon_ids or []:
            try:
                addon_id = int(addon_id)
            except (TypeError, ValueError):
                raise ValidationError(_('An invalid add-on was selected.'))
            if addon_id > 0 and addon_id not in normalized_ids:
                normalized_ids.append(addon_id)

        if not normalized_ids:
            return []

        mapping_model = self.env['logspace.provider.vehicle.type.addon'].sudo()
        available_mappings = mapping_model.search([
            ('provider_id', '=', self.provider_id.id),
            ('vehicle_type_id', '=', self.vehicle_type_id.id),
            ('is_active', '=', True),
        ])

        values = []
        if available_mappings:
            selected = available_mappings.filtered(
                lambda mapping: mapping.addon_id.id in normalized_ids
            )
            if set(selected.addon_id.ids) != set(normalized_ids):
                raise ValidationError(_('One or more selected add-ons are not offered.'))
            for addon_id in normalized_ids:
                mapping = selected.filtered(lambda item: item.addon_id.id == addon_id)[:1]
                if (
                    not mapping.addon_id.active
                    or mapping.currency_id != self.currency_id
                    or mapping.provider_price < 0
                ):
                    raise ValidationError(_('An add-on has an invalid price configuration.'))
                values.append({
                    'addon': mapping.addon_id,
                    'price': mapping.provider_price,
                })
        else:
            selected = self.env['logspace.addon'].sudo().search([
                ('id', 'in', normalized_ids),
                ('active', '=', True),
            ])
            if set(selected.ids) != set(normalized_ids):
                raise ValidationError(_('One or more selected add-ons are not available.'))
            addon_by_id = {addon.id: addon for addon in selected}
            for addon_id in normalized_ids:
                addon = addon_by_id[addon_id]
                if addon.currency_id != self.currency_id or addon.price < 0:
                    raise ValidationError(_('An add-on has an invalid price configuration.'))
                values.append({'addon': addon, 'price': addon.price})

        return values
