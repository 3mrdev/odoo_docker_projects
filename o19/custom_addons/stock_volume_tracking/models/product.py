from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_volume_tracked = fields.Boolean(
        string="Track by Volume",
        help="Enable dimension tracking (Length × Width × Height) for this product. "
             "When enabled, dimensions can be specified on purchase orders and lots.",
        default=False,
    )
    is_cost_tracked = fields.Boolean(
        string="Track by Volume & Cost",
        help="Enable dimension and cost tracking for this product.",
    )

    max_volume_length = fields.Float(
        string='Max Length',
        digits='Volume',
        help="Max Length dimension of the product",
    )
    min_volume_length = fields.Float(
        string='Min Length',
        digits='Volume',
        help="Min Length dimension of the product",
    )
    max_volume_width = fields.Float(
        string='Max Width',
        digits='Volume',
        help="Max Width dimension of the product",
    )
    min_volume_width = fields.Float(
        string='Min Width',
        digits='Volume',
        help="Min Width dimension of the product",
    )
    max_volume_height = fields.Float(
        string='Max Height',
        digits='Volume',
        help="Max Height dimension of the product",
    )
    min_volume_height = fields.Float(
        string='Min Height',
        digits='Volume',
        help="Min Height dimension of the product",
    )

    @api.constrains('tracking','lot_valuated')
    def _validate_volume_and_cost_tracking(self):
        for product in self:
            if product.tracking == 'none' and product.is_volume_tracked:
                product.is_volume_tracked = False
            if not product.lot_valuated and product.is_cost_tracked:
                product.is_cost_tracked = False
