# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    property_analytic_plan = fields.Many2one(
        'account.analytic.plan',
        string='Property Analytic Plan',
        config_parameter="sale_subscription_property.default_analytic_plan_property",
    )
