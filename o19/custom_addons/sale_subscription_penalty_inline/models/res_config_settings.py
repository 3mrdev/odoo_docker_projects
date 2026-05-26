# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    penalty_amount = fields.Float(
        string="Subscription Late Payment Penalty Amount",
        config_parameter='sale_subscription_penalty_inline.penalty_amount',
        default=0.0,
        help="If more than 1 its a fixed amount and if its between 0 and 1 its a percentage of the total amount to charge as penalty for late subscription payments"
    )
    
    penalty_product_id = fields.Many2one(
        'product.product',
        string="Penalty Product",
        config_parameter='sale_subscription_penalty_inline.penalty_product_id',
        domain=[('type', '=', 'service')],
        help="Product to use for penalty invoice lines"
    )
