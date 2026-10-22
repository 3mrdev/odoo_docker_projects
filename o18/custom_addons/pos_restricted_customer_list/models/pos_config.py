# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.osv import expression


class PosConfig(models.Model):
    _inherit = "pos.config"

    pos_partner_category = fields.Boolean(string="Filter partner from category")
    partner_category_id = fields.Many2one(
        string="Customer tag",
        help="Partner tag allowing to show only customers who belong to it.",
        comodel_name="res.partner.category",
        ondelete="restrict",
        required=False,
    )
    available_in_pos_restricted = fields.Boolean(
        compute="_compute_available_in_pos_restricted"
    )

    def _compute_available_in_pos_restricted(self):
        for config in self:
            config.available_in_pos_restricted = True

    def get_limited_partners_loading(self):
        # Odoo 18 core preloads only the top `limited_customer_count` (default 100)
        # partners ordered by POS order count/name. With the customer-list
        # restriction active, all partners flagged available_in_pos must be
        # preloaded at session load instead.
        self.ensure_one()
        Partner = self.env["res.partner"]
        domain = expression.AND(
            [
                Partner._pos_restricted_partner_domain(self),
                ["|", ("company_id", "=", self.company_id.id), ("company_id", "=", False)],
            ]
        )
        return [(partner.id,) for partner in Partner.search(domain)]
