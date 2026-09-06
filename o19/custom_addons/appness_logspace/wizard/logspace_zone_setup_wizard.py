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
        required=True,
        domain=[('is_provider', '=', True)],
        default=lambda self: self.env.context.get('default_provider_id'),
    )

    zone_ids = fields.Many2many(
        'logspace.zone',
        'logspace_zone_setup_wizard_zone_rel',
        'wizard_id', 'zone_id',
        string='Operating Zones',
        help='Select the exact zones where this provider operates. '
             'Routes are generated only between the zones you select here. '
             'The portal search handles hierarchy automatically.',
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

    # ---- Preview ----
    estimated_routes = fields.Integer(
        string='Estimated Routes',
        compute='_compute_estimated_routes',
    )

    @api.depends('zone_ids', 'vehicle_type_ids')
    def _compute_estimated_routes(self):
        for wiz in self:
            n_zones = len(wiz.zone_ids)
            n_vtypes = len(wiz.vehicle_type_ids)
            # permutations(n, 2) = n * (n - 1)
            wiz.estimated_routes = max(0, n_zones * (n_zones - 1) * n_vtypes)

    # -------------------------------------------------------------------------
    # Helper buttons
    # -------------------------------------------------------------------------
    def select_all_zones(self):
        """Select all governorate-level zones (top-level zones only).

        Since the portal search handles hierarchy, selecting governorates
        is enough to cover all their child zones.
        """
        self.ensure_one()
        governorates = self.env['logspace.zone'].search([
            ('active', '=', True),
            ('zone_type', '=', 'governorate'),
        ])
        self.zone_ids = [(6, 0, governorates.ids)]
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def select_my_zones(self):
        """Pre-select zones where this provider already has vehicles."""
        self.ensure_one()
        if not self.provider_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Provider'),
                    'message': _('Please select a provider first.'),
                    'type': 'warning',
                    'sticky': False,
                },
            }
        vehicles = self.env['logspace.vehicle'].search([
            ('provider_id', '=', self.provider_id.id),
        ])
        zones = vehicles.mapped('zone_id').filtered('active')
        if zones:
            self.zone_ids = [(6, 0, zones.ids)]
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
    def _get_selected_zones(self):
        """Return only the explicitly selected zones (no child expansion).

        The portal search uses _get_zone_hierarchy_ids() to walk UP/DOWN
        the zone tree, so a city-level price matrix row automatically
        covers all its child districts during customer search.
        """
        self.ensure_one()
        return self.zone_ids

    # -------------------------------------------------------------------------
    # Confirm action
    # -------------------------------------------------------------------------
    def action_confirm(self):
        """Generate or update price matrix entries for all zone pair combinations.

        Only the explicitly selected zones are used (no child expansion).
        Existing entries are updated with the new rates instead of being skipped.
        """
        self.ensure_one()

        if not self.zone_ids:
            raise UserError(_('Please select at least one zone.'))
        if not self.vehicle_type_ids:
            raise UserError(_('Please select at least one vehicle type.'))

        provider = self.provider_id
        selected_zones = self._get_selected_zones()
        DistanceModel = self.env['logspace.zone.distance']
        PriceMatrix = self.env['logspace.price.matrix']

        created_count = 0
        updated_count = 0

        # Pre-load existing price matrix entries for this provider + zones
        # This replaces per-permutation DB hits with a single query
        existing_matrices = PriceMatrix.search_read([
            ('provider_id', '=', provider.id),
            ('vehicle_type_id', 'in', self.vehicle_type_ids.ids),
            ('zone_from_id', 'in', selected_zones.ids),
            ('zone_to_id', 'in', selected_zones.ids),
        ], fields=['vehicle_type_id', 'zone_from_id', 'zone_to_id'])

        # Build lookup: (vtype_id, zone_from_id, zone_to_id) -> record_id
        existing_map = {
            (m['vehicle_type_id'][0], m['zone_from_id'][0], m['zone_to_id'][0]): m['id']
            for m in existing_matrices
        }

        for vtype in self.vehicle_type_ids:
            for zone_from, zone_to in permutations(selected_zones, 2):
                # Lookup distance from the zone distance matrix
                distance_km = DistanceModel.get_distance(zone_from, zone_to)

                # Calculate provider price
                provider_price = self.base_rate + (distance_km * self.per_km_rate)
                if provider_price < 0:
                    provider_price = 0.0

                # Check if entry already exists (from pre-loaded dict)
                existing_id = existing_map.get((vtype.id, zone_from.id, zone_to.id))

                if existing_id:
                    # Update existing entry with new rates
                    PriceMatrix.browse(existing_id).write({
                        'distance_km': distance_km,
                        'provider_price': round(provider_price, 2),
                        'is_active': True,
                    })
                    updated_count += 1
                else:
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

        total = created_count + updated_count
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Zone Setup Complete'),
                'message': _(
                    'Created %(created)d new routes. '
                    'Updated %(updated)d existing routes. '
                    'Total: %(total)d routes.'
                ) % {
                    'created': created_count,
                    'updated': updated_count,
                    'total': total,
                },
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
