# -*- coding: utf-8 -*-

from odoo import models, fields, api

class GenerateUnitsWizard(models.TransientModel):
    _name = 'jiz.waqf.generate.units.wizard'
    _description = 'Generate Waqf Units Wizard'

    waqf_id = fields.Many2one('jiz.waqf', string='Waqf', required=True)
    number_of_units = fields.Integer(string='Number of Units', default=1, required=True)
    product_id = fields.Many2one('product.product', string='Unit Product', required=True, domain="[('type', '=', 'service')]")
    unit_price = fields.Float(string='Unit Price', required=True)

    def action_generate_units(self):
        for i in range(self.number_of_units):
            self.env['jiz.waqf.unit'].create({
                'waqf_id': self.waqf_id.id,
                'product_id': self.product_id.id,
                'price': self.unit_price,
            })