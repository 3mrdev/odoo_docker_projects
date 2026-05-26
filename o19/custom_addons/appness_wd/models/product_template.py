from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pos_config_ids = fields.Many2many(
        'pos.config',
        string="Available in Specific POS",
        help="Restrict the availability of this product to specific Point of Sale configurations. "
             "If empty, the product is available in all POS sessions."
    )

    @api.model
    def _load_pos_data_domain(self, data, config):
        domain = super()._load_pos_data_domain(data, config)
        if config.id:
            domain += ['|', ('pos_config_ids', '=', False), ('pos_config_ids', 'in', config.id)]
        return domain
