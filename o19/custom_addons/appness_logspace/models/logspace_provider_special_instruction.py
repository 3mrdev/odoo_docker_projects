# -*- coding: utf-8 -*-

from odoo import models, fields


class LogspaceProviderSpecialInstruction(models.Model):
    """Provider Special Instructions by Vehicle Type

    Allows providers to set custom instructions that will be shown to customers
    for each vehicle type they offer. These can include handling requirements,
    equipment included, restrictions, or any other important information.
    """
    _name = 'logspace.provider.special.instruction'
    _description = 'Provider Special Instructions by Vehicle Type'
    _rec_name = 'vehicle_type_id'
    _order = 'partner_id, vehicle_type_id'

    # =========================================================================
    # Relations
    # =========================================================================
    partner_id = fields.Many2one(
        'res.partner',
        string='Provider',
        required=True,
        domain=[('is_provider', '=', True)],
        ondelete='cascade',
        index=True
    )
    vehicle_type_id = fields.Many2one(
        'logspace.vehicle.type',
        string='Vehicle Type',
        required=True,
        index=True
    )

    # =========================================================================
    # Content
    # =========================================================================
    instructions = fields.Html(
        string='Special Instructions',
        help='Instructions shown to customers for this vehicle type. '
             'Examples: "All trucks include securing straps and tarps", '
             '"Refrigerated trucks maintain 2-4°C", '
             '"Maximum item length: 3 meters", etc.'
    )

    # =========================================================================
    # Status
    # =========================================================================
    is_active = fields.Boolean(
        string='Active',
        default=True,
        help='Only active instructions are shown to customers'
    )

    # =========================================================================
    # Related Fields
    # =========================================================================
    partner_state = fields.Selection(
        related='partner_id.state',
        string='Provider State',
        store=True
    )

    # =========================================================================
    # Constraints
    # =========================================================================
    _unique_instruction_vehicle = models.Constraint(
        'unique(partner_id, vehicle_type_id)',
        'Special instructions for this vehicle type already exist!',
    )
