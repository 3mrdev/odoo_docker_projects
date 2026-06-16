# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from itertools import permutations


class LogspaceZoneSetupWizard(models.TransientModel):
    """
    Provider Zone Setup Wizard.

    Lets a provider quickly configure which zones they operate in and which
    vehicle types they offer.  On confirm the wizard generates
    logspace.price.matrix entries for every zone-pair permutation, using
    distances from the logspace.zone.distance matrix and the pricing rates
    entered in the wizard.
    """
    _name = 'logspace.zone.setup.wizard'
    _description = 'Logspace Zone Setup Wizard'

    provider_id = fields.Many2one(
        'res.partner', string='Provider',
        required=True, readonly=True,
        domain=[('is_provider', '=', True)],
        default=lambda self: self.env.context.get('default_provider_id'),
    )

    zone_ids = fields.Many2many(
        'logspace.zone',
        'logspace_zone_setup_wizard_zone_rel',
        'wizard_id', 'zone_id',
        string='Operating Zones',
        help='Select zones where this provider operates. '
             'Child zones of selected governorates will be included automatically.',
    )

    vehicle_type_ids = fields.Many2many(
        'logspace.vehicle.type',
        'logspace_zone_setup_wizard_vtype_rel',
        'wizard_id', 'vehicle_type_id',
        string='Vehicle Types',
        help='Select vehicle types this provider offers.',
    )

    # ---- Pricing configuration ----
    base_rate = fields.Float(
        string='Base Rate',
        default=2.0,
        help='Fixed base price added to every route (in company currency)',
    )
    per_km_rate = fields.Float(
        string='Per KM Rate',
        default=0.5,
        help='Price per estimated kilometre. '
             'Formula: provider_price = base_rate + (estimated_km x per_km_rate)',
    )

    # -------------------------------------------------------------------------
    # Helper buttons
    # -------------------------------------------------------------------------
    def select_all_zones(self):
        """Select all active zones."""
        self.ensure_one()
        all_zones = self.env['logspace.zone'].search([('active', '=', True)])
        self.zone_ids = [(6, 0, all_zones.ids)]
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def deselect_all_zones(self):
        """Clear all zone selections."""
        self.ensure_one()
        self.zone_ids = [(5, 0, 0)]
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------
    def _get_all_zones(self):
        """Return selected zones + all their child zones (deduplicated)."""
        self.ensure_one()
        all_zones = self.env['logspace.zone']
        for zone in self.zone_ids:
            all_zones |= zone
            if zone.child_ids:
                all_zones |= zone.child_ids
        return all_zones

    # -------------------------------------------------------------------------
    # Confirm action
    # -------------------------------------------------------------------------
    def action_confirm(self):
        """Generate price matrix entries for all zone pair combinations."""
        self.ensure_one()

        if not self.zone_ids:
            raise UserError(_('Please select at least one zone.'))
        if not self.vehicle_type_ids:
            raise UserError(_('Please select at least one vehicle type.'))

        provider = self.provider_id
        all_zones = self._get_all_zones()
        zone_ids = all_zones.ids
        DistanceModel = self.env['logspace.zone.distance']
        PriceMatrix = self.env['logspace.price.matrix']

        created_count = 0
        skipped_count = 0

        for vtype in self.vehicle_type_ids:
            for zone_from, zone_to in permutations(all_zones, 2):
                # Skip if already exists
                existing = PriceMatrix.search([
                    ('provider_id', '=', provider.id),
                    ('vehicle_type_id', '=', vtype.id),
                    ('zone_from_id', '=', zone_from.id),
                    ('zone_to_id', '=', zone_to.id),
                ], limit=1)
                if existing:
                    skipped_count += 1
                    continue

                # Lookup distance from the zone distance matrix
                distance_km = DistanceModel.get_distance(zone_from, zone_to)

                # Calculate provider price
                provider_price = self.base_rate + (distance_km * self.per_km_rate)
                if provider_price < 0:
                    provider_price = 0.0

                PriceMatrix.create({
                    'provider_id': provider.id,
                    'vehicle_type_id': vtype.id,
                    'zone_from_id': zone_from.id,
                    'zone_to_id': zone_to.id,
                    'distance_km': distance_km,
                    'provider_price': round(provider_price, 2),
                    'is_active': True,
                })
                created_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Zone Setup Complete'),
                'message': _(
                    'Created %(created)d price matrix entries. '
                    'Skipped %(skipped)d existing entries.'
                ) % {'created': created_count, 'skipped': skipped_count},
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
