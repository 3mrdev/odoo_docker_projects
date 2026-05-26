from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    flavor_value_limit_enabled = fields.Boolean(
        string="Flavor Value Limit",
        default=False,
        help="Enable per-value maximum limit in the flavor mix popup.",
    )
    flavor_clickable_card_enabled = fields.Boolean(
        string="Flavor Clickable Card",
        default=False,
        help="Make flavor cards clickable to increment quantity in the POS popup.",
    )
    flavor_multi_attribute_enabled = fields.Boolean(
        string="Flavor Multi Attribute",
        default=False,
        help="Show multiple attribute groups in the flavor mix popup.",
    )
