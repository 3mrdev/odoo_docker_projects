from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    subscription_expiry_domain = fields.Char(
        string="Subscription Expiry Domain",
        config_parameter='sale_subscription_expire.subscription_expiry_domain',
        default='[("state", "=", "sale"),("subscription_state", "=", "3_progress")]',
        help="Domain to filter subscription orders"
    )