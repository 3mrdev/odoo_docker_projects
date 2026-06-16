# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class LogspaceZoneDistance(models.Model):
    """Zone Distance Matrix - stores estimated km between zones (offline, no API)"""
    _name = 'logspace.zone.distance'
    _description = 'Logspace Zone Distance Matrix'
    _order = 'zone_from_id, zone_to_id'
    _rec_name = 'display_name'

    zone_from_id = fields.Many2one(
        'logspace.zone', string='From Zone',
        required=True, ondelete='cascade', index=True,
    )
    zone_to_id = fields.Many2one(
        'logspace.zone', string='To Zone',
        required=True, ondelete='cascade', index=True,
    )
    estimated_km = fields.Float(
        string='Estimated Distance (km)', required=True,
        help='Estimated road distance between the two zones',
    )
    estimated_minutes = fields.Integer(
        string='Estimated Time (min)',
        help='Estimated travel time in minutes (optional)',
    )
    active = fields.Boolean(default=True, string='Active')

    display_name = fields.Char(
        string='Route', compute='_compute_display_name', store=True,
    )

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------
    _route_unique = models.Constraint(
        'unique(zone_from_id, zone_to_id)',
        'Distance already exists for this zone pair!',
    )

    @api.constrains('zone_from_id', 'zone_to_id')
    def _check_different_zones(self):
        for rec in self:
            if rec.zone_from_id == rec.zone_to_id:
                raise models.ValidationError(
                    _('From Zone and To Zone must be different.')
                )

    # -------------------------------------------------------------------------
    # Compute
    # -------------------------------------------------------------------------
    @api.depends('zone_from_id', 'zone_to_id')
    def _compute_display_name(self):
        for rec in self:
            from_name = rec.zone_from_id.name or ''
            to_name = rec.zone_to_id.name or ''
            rec.display_name = f"{from_name} → {to_name}"

    # -------------------------------------------------------------------------
    # CRUD overrides — symmetric auto-create
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self._ensure_symmetric(records)
        return records

    def write(self, vals):
        result = super().write(vals)
        if 'estimated_km' in vals or 'estimated_minutes' in vals:
            self._ensure_symmetric(self)
        return result

    def _ensure_symmetric(self, records):
        """For each A→B record, ensure B→A exists with the same values."""
        for rec in records:
            reverse = self.search([
                ('zone_from_id', '=', rec.zone_to_id.id),
                ('zone_to_id', '=', rec.zone_from_id.id),
            ], limit=1)
            if not reverse:
                # Create mirror record (bypass the symmetric trigger to avoid loop)
                super(LogspaceZoneDistance, self).create({
                    'zone_from_id': rec.zone_to_id.id,
                    'zone_to_id': rec.zone_from_id.id,
                    'estimated_km': rec.estimated_km,
                    'estimated_minutes': rec.estimated_minutes,
                    'active': rec.active,
                })
            elif reverse.estimated_km != rec.estimated_km or \
                    reverse.estimated_minutes != rec.estimated_minutes:
                super(LogspaceZoneDistance, reverse).write({
                    'estimated_km': rec.estimated_km,
                    'estimated_minutes': rec.estimated_minutes,
                })

    # -------------------------------------------------------------------------
    # Distance lookup with hierarchical parent-walk fallback
    # -------------------------------------------------------------------------
    @api.model
    def get_distance(self, zone_from, zone_to):
        """
        Return estimated km between two zones.

        Fallback chain (iterative, no recursion):
          1. Exact pair  A → B
          2. Reverse     B → A
          3. Walk parents level-by-level (max depth 5):
             A.parent → B,  A → B.parent,  A.parent → B.parent
          4. Same zone   → 5.0 km (default short distance)
          5. No match    → 0.0
        """
        if not zone_from or not zone_to:
            return 0.0

        # Same zone — short default
        if zone_from.id == zone_to.id:
            return 5.0

        # 1. Direct lookup A → B
        rec = self.search([
            ('zone_from_id', '=', zone_from.id),
            ('zone_to_id', '=', zone_to.id),
        ], limit=1)
        if rec:
            return rec.estimated_km

        # 2. Reverse lookup B → A (kept for safety; symmetric create should cover this)
        rec = self.search([
            ('zone_from_id', '=', zone_to.id),
            ('zone_to_id', '=', zone_from.id),
        ], limit=1)
        if rec:
            return rec.estimated_km

        # 3. Iterative parent-walk: move up the hierarchy level-by-level
        MAX_DEPTH = 5
        zf = zone_from
        zt = zone_to
        for _ in range(MAX_DEPTH):
            # Try parent of from-zone against current to-zone
            if zf.parent_id:
                rec = self.search([
                    ('zone_from_id', '=', zf.parent_id.id),
                    ('zone_to_id', '=', zt.id),
                ], limit=1)
                if rec:
                    return rec.estimated_km
                # Also try reverse
                rec = self.search([
                    ('zone_from_id', '=', zt.id),
                    ('zone_to_id', '=', zf.parent_id.id),
                ], limit=1)
                if rec:
                    return rec.estimated_km

            # Try current from-zone against parent of to-zone
            if zt.parent_id:
                rec = self.search([
                    ('zone_from_id', '=', zf.id),
                    ('zone_to_id', '=', zt.parent_id.id),
                ], limit=1)
                if rec:
                    return rec.estimated_km
                # Also try reverse
                rec = self.search([
                    ('zone_from_id', '=', zt.parent_id.id),
                    ('zone_to_id', '=', zf.id),
                ], limit=1)
                if rec:
                    return rec.estimated_km

            # Try both parents
            if zf.parent_id and zt.parent_id:
                rec = self.search([
                    ('zone_from_id', '=', zf.parent_id.id),
                    ('zone_to_id', '=', zt.parent_id.id),
                ], limit=1)
                if rec:
                    return rec.estimated_km

            # Move up one level
            if zf.parent_id:
                zf = zf.parent_id
            if zt.parent_id:
                zt = zt.parent_id
            # Stop if both have no more parents
            if not zf.parent_id and not zt.parent_id:
                break

        # 4. No match found
        return 0.0
