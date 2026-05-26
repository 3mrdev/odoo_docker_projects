# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class LogspaceProviderVehicleTypeAddon(models.Model):
    """Provider Vehicle Type Addon - Maps provider-specific add-ons to a vehicle type.
    
    This model allows each provider to define their own set of add-ons
    per vehicle type. When a vehicle type is added to a provider's fleet,
    these add-ons become available for that vehicle type.
    """
    _name = 'logspace.provider.vehicle.type.addon'
    _description = 'Provider Vehicle Type Add-on'
    _order = 'provider_id, vehicle_type_id, sequence'
    _rec_name = 'display_name'

    provider_id = fields.Many2one(
        'res.partner', string='Provider',
        required=True, ondelete='cascade', index=True,
        domain=[('is_provider', '=', True)])
    vehicle_type_id = fields.Many2one(
        'logspace.vehicle.type', string='Vehicle Type',
        required=True, ondelete='cascade', index=True)
    addon_id = fields.Many2one(
        'logspace.addon', string='Add-on',
        required=True, ondelete='restrict',
        help='The add-on service available for this vehicle type')
    
    # Provider-specific pricing (overrides the master add-on price)
    provider_price = fields.Float(
        string='Provider Price', required=True, default=0.0,
        help='Provider-specific price for this add-on (overrides master price)')
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id)
    
    # Availability
    is_active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # Related fields for display
    addon_description = fields.Text(
        related='addon_id.description', string='Description', readonly=True)
    addon_icon = fields.Char(
        related='addon_id.icon', string='Icon', readonly=True)
    master_price = fields.Float(
        related='addon_id.price', string='Master Price', readonly=True)
    
    # Computed
    display_name = fields.Char(
        string='Display Name', compute='_compute_display_name', store=True)

    @api.depends('provider_id.name', 'vehicle_type_id.name', 'addon_id.name')
    def _compute_display_name(self):
        for rec in self:
            parts = [
                rec.provider_id.name or '',
                rec.vehicle_type_id.name or '',
                rec.addon_id.name or '',
            ]
            rec.display_name = ' / '.join(filter(None, parts))

    @api.onchange('addon_id')
    def _onchange_addon_id(self):
        """Pre-fill price from master add-on"""
        if self.addon_id:
            self.provider_price = self.addon_id.price

    _unique_provider_vtype_addon = models.Constraint(
        'unique(provider_id, vehicle_type_id, addon_id)',
        'An add-on can only be assigned once per provider and vehicle type!')
