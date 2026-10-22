# Copyright 2017-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    available_in_pos = fields.Boolean(
        string="Available for POS",
        default=False,
    )

    @api.model
    def _pos_restricted_partner_domain(self, config):
        domain = [("available_in_pos", "=", True)]
        if config.pos_partner_category and config.partner_category_id:
            domain.append(("category_id", "in", config.partner_category_id.ids))
        return domain

    @api.model
    def _load_pos_data_domain(self, data):
        domain = super()._load_pos_data_domain(data)
        config_id = self.env["pos.config"].browse(data["pos.config"]["data"][0]["id"])
        return domain + self._pos_restricted_partner_domain(config_id)

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        fields.append("available_in_pos")
        return fields
