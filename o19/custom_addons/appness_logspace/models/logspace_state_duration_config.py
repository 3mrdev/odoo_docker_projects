# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class LogspaceStateDurationConfig(models.Model):
    """Per-state duration configuration for timeline estimation.

    Travel states (pickup_started, arrived_destination) derive their duration
    from the zone distance record (estimated_minutes or km-based fallback).
    All other states use the fixed duration_minutes value configured here.
    """
    _name = 'logspace.state.duration.config'
    _description = 'Logspace State Duration Configuration'
    _order = 'sequence, id'

    state_key = fields.Selection([
        ('order_received', 'Order Received'),
        ('pickup_started', 'Pickup Started (Driver Dispatched)'),
        ('vendor_arrived_pickup', 'Vendor Arrived at Pickup (Travel Duration)'),
        ('pickup_addons', 'Pickup Add-ons Performed'),
        ('pickup_completed', 'Pickup Completed'),
        ('pre_dropoff_addons', 'Pre-Drop-off Add-ons (Dropoff Leg Start)'),
        ('arrived_destination', 'Arrived at Destination (Travel Duration)'),
        ('dropoff_completed', 'Drop-off Completed'),
        ('grace_period', 'Grace Period'),
        ('order_completed', 'Order Completed'),
    ], string='Workflow State', required=True, index=True)

    duration_minutes = fields.Integer(
        string='Duration (min)',
        required=True,
        default=5,
        help='Estimated duration in minutes for this state. '
             'Ignored for arrival states (Vendor Arrived at Pickup, Arrived at Destination) '
             'which use zone distance data instead.',
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    notes = fields.Char(string='Notes')

    _state_key_unique = models.Constraint(
        'unique(state_key)',
        'A configuration already exists for this state.',
    )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    # States whose duration comes from the zone distance record (travel time)
    TRAVEL_STATES = {'pickup_started', 'arrived_destination'}

    @api.model
    def get_duration_map(self):
        """Return {state_key: duration_minutes} for all active records."""
        records = self.search([])
        return {r.state_key: r.duration_minutes for r in records}

    @api.model
    def get_duration(self, state_key):
        """Return duration_minutes for a single state key (0 if not found)."""
        rec = self.search([('state_key', '=', state_key)], limit=1)
        return rec.duration_minutes if rec else 0
