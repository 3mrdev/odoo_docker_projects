from odoo import fields, models


class StockRoute(models.Model):
    _inherit = 'stock.route'

    boolean_route_flag = fields.Boolean(
        string='Route Flag', default=False)


class StockRule(models.Model):
    _inherit = 'stock.rule'

    boolean_rule_flag = fields.Boolean(
        string='Rule Flag', default=False)
