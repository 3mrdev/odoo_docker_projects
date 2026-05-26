from odoo import models, fields, api


class ApprovalProductLine(models.Model):
    _inherit = 'approval.product.line'

    # ==========================================================================
    # EXTEND COMPUTE METHODS FOR COMBINED TYPE
    # ==========================================================================
    @api.depends('approval_request_id.approval_type', 'product_uom_id', 'quantity')
    def _compute_po_uom_qty(self):
        """Override to compute po_uom_qty for stock_material_purchase type as well."""
        for line in self:
            approval_type = line.approval_request_id.approval_type
            if approval_type in ('purchase', 'stock_material_purchase') and line.product_id and line.quantity:
                uom = line.product_uom_id or line.product_id.uom_id
                line.po_uom_qty = uom._compute_quantity(
                    line.quantity,
                    line.product_id.uom_id,
                )
            else:
                line.po_uom_qty = 0.0

    def _domain_product_id(self):
        """Override to handle combined type - only storable + purchasable products."""
        # Check for combined type first
        if self.env.context.get('default_category_id'):
            category = self.env['approval.category'].browse(
                self.env.context['default_category_id']
            )
            if category.approval_type == 'stock_material_purchase':
                # Combined type: must be BOTH storable AND purchasable
                return [
                    ('type', '=', 'product'),       # Storable (for stock transfer)
                    ('purchase_ok', '=', True),      # Purchasable (for PO)
                ]

        # For stock_material type (original behavior)
        if self.env.context.get('default_category_id'):
            category = self.env['approval.category'].browse(
                self.env.context['default_category_id']
            )
            if category.approval_type == 'stock_material':
                return [('type', '=', 'product')]

        # For purchase type (from approvals_purchase context handling)
        if 'default_category_id' in self.env.context:
            category_id = self.env.context.get('default_category_id')
        elif self.env.context.get('active_model') == 'approval.category':
            category_id = self.env.context.get('active_id')
        else:
            return []

        if category_id:
            category = self.env['approval.category'].browse(category_id)
            if category.approval_type == 'purchase':
                return [('purchase_ok', '=', True)]

        return []

    # Override product_id domain to use our dynamic domain method
    product_id = fields.Many2one(domain=lambda self: self._domain_product_id())
