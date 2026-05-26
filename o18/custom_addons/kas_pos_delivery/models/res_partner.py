# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    use_pos_customer_account = fields.Boolean(
        string='Use POS Customer Account',
        default=False,
        help='When enabled, clicking Payment in POS will automatically use Customer Account payment method and skip the payment screen.',
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Extend POS data fields to include use_pos_customer_account for frontend access."""
        result = super()._load_pos_data_fields(config_id)
        result.append('use_pos_customer_account')
        return result
