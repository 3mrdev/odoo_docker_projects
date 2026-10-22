from odoo import models, fields, api, _


class ApprovalProductLine(models.Model):
    _inherit = 'approval.product.line'

    def _domain_product_id(self):
        """Filter products that are available for stock transfer."""
        if self.env.context.get('default_category_id'):
            category = self.env['approval.category'].browse(self.env.context['default_category_id'])
            if category.approval_type == 'stock_material':
                return [('is_storable', '=', True)]  # Only storable products
        return []

    # Domain for stock material - only allow storable products
    product_id = fields.Many2one(domain=lambda self: self._domain_product_id())
