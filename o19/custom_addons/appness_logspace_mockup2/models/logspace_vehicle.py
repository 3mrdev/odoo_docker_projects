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


