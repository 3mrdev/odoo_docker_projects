# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# License URL : https://store.webkul.com/license.html/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class ComboProduct(models.Model):
    _inherit = 'product.combo'

    marketplace_seller_id = fields.Many2one("res.partner", string="Marketplace Seller", default=lambda self:
                                            self.env.user.partner_id.id if self.env.user.partner_id and self.env.user.partner_id.seller else self.env['res.partner'], copy=False,)

    @api.onchange('marketplace_seller_id')
    def _onchange_mp_seller(self):
        self.write({'combo_item_ids': [(fields.Command.clear())]})
