# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Marks the vendor bills this module creates as provider commission bills.
    # The Provider Bills menu filters on this instead of
    # ('partner_id.is_provider', '=', True): a dotted domain on a model the
    # provider can only partly read makes the action's scope depend on how the
    # ORM applies res.partner's record rules through the join, which is not
    # something a menu should rely on.
    is_logspace_provider_bill = fields.Boolean(
        string='Logspace Provider Bill', readonly=True, copy=False, index=True)
