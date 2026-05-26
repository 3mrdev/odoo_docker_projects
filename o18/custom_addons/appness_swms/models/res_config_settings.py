from odoo import _, api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pause_days = fields.Integer(string="Pause Sponserships After (Days)", default=30, config_parameter='appness_swms.pause_days')
    orphan_age = fields.Integer(string="Orphan Sponsership Age (Years)", default=18, config_parameter='appness_swms.orphan_age')
    needy_family_period = fields.Integer(string="Needy Family Sponsership Period (Months)", default=6, config_parameter='appness_swms.needy_family_period')
    family_analytic_plan = fields.Many2one("account.analytic.plan",string="Families Analytic Plan", config_parameter='appness_swms.family_analytic_plan',required=True)