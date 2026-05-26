from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_flavor_value_limit_enabled = fields.Boolean(
        related='pos_config_id.flavor_value_limit_enabled',
        readonly=False,
    )
    pos_flavor_clickable_card_enabled = fields.Boolean(
        related='pos_config_id.flavor_clickable_card_enabled',
        readonly=False,
    )
    pos_flavor_multi_attribute_enabled = fields.Boolean(
        related='pos_config_id.flavor_multi_attribute_enabled',
        readonly=False,
    )
