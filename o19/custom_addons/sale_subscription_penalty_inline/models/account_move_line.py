# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_penalty_line = fields.Boolean(
        string="Is Penalty Line",
        default=False,
        help="Indicates this line is a penalty charge for late payment",
        copy=False
    )
