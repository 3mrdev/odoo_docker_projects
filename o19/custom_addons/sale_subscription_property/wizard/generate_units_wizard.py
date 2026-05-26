# -*- coding: utf-8 -*-

from odoo import models, fields, api

class GenerateUnitsWizard(models.TransientModel):
    _name = 'hrb.property.generate.units.wizard'
    _description = 'Generate Property Units Wizard'

    property_id = fields.Many2one('hrb.property', string='Property', required=True)
    number_of_units = fields.Integer(string='Number of Units', default=1, required=True)
    product_id = fields.Many2one('product.product', string='Unit Product', required=True, domain="[('type', '=', 'service')]")
    unit_price = fields.Float(string='Unit Price', required=True)

    def action_generate_units(self):
        for i in range(self.number_of_units):
            self.env['hrb.property.unit'].create({
                'property_id': self.property_id.id,
                'product_id': self.product_id.id,
                'price': self.unit_price,
            })