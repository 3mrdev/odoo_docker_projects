# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta

class PosConfig(models.Model):
    _inherit = 'pos.config'

    return_limit_days = fields.Integer(string="Return Limit (Days)", default=0, help="Number of days after which products cannot be returned. Set to 0 for no limit.")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_return_limit_days = fields.Integer(related='pos_config_id.return_limit_days', readonly=False)

class PosOrder(models.Model):
    _inherit = 'pos.order'

    def refund(self):
        for order in self:
            if order.config_id.return_limit_days > 0:
                limit_date = fields.Date.today() - timedelta(days=order.config_id.return_limit_days)
                if order.date_order.date() < limit_date:
                    raise UserError(_("This order can't be returned due to our policy of not returning products after %s amount of days") % order.config_id.return_limit_days)
        
        return super(PosOrder, self).refund()
