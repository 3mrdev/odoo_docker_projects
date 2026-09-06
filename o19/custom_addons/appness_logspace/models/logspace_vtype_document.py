# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LogspaceVehicleTypeDocument(models.Model):
    """Required documents that a vehicle type asks from customers"""
    _name = 'logspace.vehicle.type.document'
    _description = 'Vehicle Type Required Documents'
    _order = 'vehicle_type_id, sequence'

    vehicle_type_id = fields.Many2one(
        'logspace.vehicle.type',
        string='Vehicle Type',
        required=True,
        ondelete='cascade',
        index=True
    )
    name = fields.Char(string='Document Name', required=True, translate=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    is_active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_vtype_document',
         'unique(vehicle_type_id, name)',
         'This document name already exists for this vehicle type!')
    ]
