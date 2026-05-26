from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    # Manual route selection - admin decides which routes user sees
    allowed_route_ids = fields.Many2many(
        'stock.route',
        string='Available Routes'
    )
