# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class LogspaceProviderTimeFrame(models.Model):
    """Provider Available Time Slots - multi-select per vehicle type"""
    _name = 'logspace.provider.time.frame'
    _description = 'Provider Available Time Frames'
    _rec_name = 'display_name'
    _order = 'partner_id, vehicle_type_id'

    partner_id = fields.Many2one(
        'res.partner', string='Provider', required=True,
        domain=[('is_provider', '=', True)],
        ondelete='cascade', index=True)
    vehicle_type_id = fields.Many2one(
        'logspace.vehicle.type', string='Vehicle Type',
        required=True, index=True)
    time_slot_ids = fields.Many2many(
        'logspace.time.slot', 'logspace_provider_timeframe_slot_rel',
        'timeframe_id', 'slot_id',
        string='Available Time Slots')

    display_name = fields.Char(
        string='Time Slots', compute='_compute_display_name', store=True)
    name = fields.Char(
        string='Name (compat)', compute='_compute_display_name', store=True)

    @api.depends('time_slot_ids')
    def _compute_display_name(self):
        for tf in self:
            slots = tf.time_slot_ids.sorted('sequence')
            tf.display_name = ', '.join(slots.mapped('name')) if slots else ''
            tf.name = tf.display_name

    _sql_constraints = [
        ('unique_provider_vtype',
         'unique(partner_id, vehicle_type_id)',
         'This vehicle type is already configured for this provider!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """Prevent duplicates - merge into existing record if found"""
        results = []
        for vals in vals_list:
            existing = self.search([
                ('partner_id', '=', vals.get('partner_id')),
                ('vehicle_type_id', '=', vals.get('vehicle_type_id')),
            ], limit=1)
            if existing:
                if vals.get('time_slot_ids'):
                    existing.time_slot_ids = [(4, sid) for _, sid, _ in vals['time_slot_ids']]
                results.append(existing)
            else:
                results.append(super().create([vals])[0])
        return results
