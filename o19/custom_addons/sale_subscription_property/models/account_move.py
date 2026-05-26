# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    property_id = fields.Many2one('hrb.property', string='Property', compute='_compute_property_details', store=True)
    property_unit_id = fields.Many2one('hrb.property.unit', string='Unit', compute='_compute_property_details', store=True)
    show_properties_features = fields.Boolean(related='company_id.show_properties_features',store=True)

    @api.depends('invoice_line_ids.sale_line_ids.order_id')
    def _compute_property_details(self):
        for move in self:
            property_id = False
            unit_id = False
            for line in move.invoice_line_ids:
                if line.sale_line_ids:
                    order = line.sale_line_ids[0].order_id
                    property_id = order.property_id.id
                    unit_id = order.property_unit_id.id
                    break
            move.property_id = property_id
            move.property_unit_id = unit_id